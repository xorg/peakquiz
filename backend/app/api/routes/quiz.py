import random
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ...db.database import get_db
from ...db.models import Game, Guess, Peak, Picture, User
from ...schemas.quiz import AnswerRequest, AnswerResult, FinishRequest, QuizSession, QuizQuestion, PeakOut
from ...api.routes.auth import get_optional_user

router = APIRouter(prefix="/quiz", tags=["quiz"])

POINTS_PER_CORRECT = 100
INITIAL_BATCH = 10
# Streak: kicks in from the 3rd consecutive correct; multiplier grows with streak length, capped.
STREAK_THRESHOLD = 3
STREAK_MAX_MULTIPLIER = 4


def _streak_multiplier(streak: int) -> int:
    if streak < STREAK_THRESHOLD:
        return 1
    return min(streak - 1, STREAK_MAX_MULTIPLIER)

# In-memory session store (replace with Redis for production)
_sessions: dict[str, dict] = {}


def _select_image(peak: Peak) -> str | None:
    """Pick a random CDN image for the peak so each quiz session may show a different photo.
    Falls back to any original_url if no CDN images exist, and returns None if the peak
    has no pictures at all."""
    cdn = [p for p in peak.pictures if p.cdn_url]
    if cdn:
        pic = random.choice(cdn)
        return pic.cdn_url.replace("/upload/", "/upload/w_800,c_limit/", 1)
    originals = [p for p in peak.pictures if p.original_url]
    if originals:
        return random.choice(originals).original_url
    return None


def _make_question(peak: Peak, all_peaks: list[Peak]) -> QuizQuestion:
    distractors = random.sample([p for p in all_peaks if p.id != peak.id], 3)
    options = [peak.name] + [d.name for d in distractors]
    random.shuffle(options)
    return QuizQuestion(
        id=peak.id,
        peak=PeakOut(
            id=peak.id,
            name=peak.name,
            imageUrl=_select_image(peak) or "",
            heightM=peak.elevation or 0,
            country=peak.region or "",
        ),
        options=options,
    )


def _eligible_peaks(db: Session) -> list[Peak]:
    return (
        db.query(Peak)
        .join(Picture)
        .filter(Picture.cdn_url.isnot(None))
        .options(joinedload(Peak.pictures))
        .distinct()
        .all()
    )


@router.post("/start", response_model=QuizSession)
def start_quiz(db: Session = Depends(get_db)):
    peaks = _eligible_peaks(db)
    if len(peaks) < 4:
        raise HTTPException(status_code=503, detail="Not enough peaks in database")

    selected = random.sample(peaks, min(INITIAL_BATCH, len(peaks)))
    questions = [_make_question(p, peaks) for p in selected]

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "answers": {q.id: q.peak.name for q in questions},
        "seen_ids": {p.id for p in selected},
        "score": 0,
        "correct_count": 0,
        "wrong_count": 0,
        "streak": 0,
        "guess_ids": [],
        # buffered for guests: flushed to DB when guestId is known at /finish
        "pending_guesses": [],
    }

    return QuizSession(sessionId=session_id, questions=questions)


@router.get("/next/{session_id}", response_model=QuizQuestion)
def next_question(session_id: str, db: Session = Depends(get_db)):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    peaks = _eligible_peaks(db)
    unseen = [p for p in peaks if p.id not in session["seen_ids"]]
    if not unseen:
        raise HTTPException(status_code=404, detail="No more peaks available")

    peak = random.choice(unseen)
    session["seen_ids"].add(peak.id)
    session["answers"][peak.id] = peak.name

    return _make_question(peak, peaks)


@router.post("/answer", response_model=AnswerResult)
def answer(
    body: AnswerRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    session = _sessions.get(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    correct_name = session["answers"].get(body.questionId)
    if correct_name is None:
        raise HTTPException(status_code=400, detail="Unknown question")

    is_correct = body.answer.strip().lower() == correct_name.strip().lower()
    points_earned = 0
    if is_correct:
        session["streak"] += 1
        multiplier = _streak_multiplier(session["streak"])
        points_earned = POINTS_PER_CORRECT * multiplier
        session["score"] += points_earned
        session["correct_count"] += 1
    else:
        session["streak"] = 0
        multiplier = 1
        session["wrong_count"] += 1

    if current_user:
        guess = Guess(user_id=current_user.id, peak_id=body.questionId, is_correct=is_correct)
        db.add(guess)
        db.flush()
        session["guess_ids"].append(guess.id)
        db.commit()
    else:
        session["pending_guesses"].append({"peak_id": body.questionId, "is_correct": is_correct})

    return AnswerResult(
        correct=is_correct,
        pointsEarned=points_earned,
        totalPoints=session["score"],
        streak=session["streak"],
        multiplier=multiplier,
    )


@router.post("/finish")
def finish_quiz(
    body: FinishRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    session = _sessions.pop(body.sessionId, None)

    if current_user:
        if body.nickname:
            current_user.username = body.nickname
        if body.score > current_user.best_score:
            current_user.best_score = body.score

        if session:
            game = Game(
                user_id=current_user.id,
                score=body.score,
                correct_count=session.get("correct_count", 0),
                wrong_count=session.get("wrong_count", 0),
            )
            db.add(game)
            db.flush()
            if session.get("guess_ids"):
                db.query(Guess).filter(Guess.id.in_(session["guess_ids"])).update(
                    {"game_id": game.id}, synchronize_session=False
                )
        db.commit()
    elif body.guestId:
        guest = db.get(User, body.guestId)
        if not guest:
            guest = User(id=body.guestId, username=body.nickname or body.guestId, best_score=body.score)
            db.add(guest)
            db.flush()
        else:
            if body.nickname:
                guest.username = body.nickname
            if body.score > guest.best_score:
                guest.best_score = body.score

        if session:
            for pg in session.get("pending_guesses", []):
                guess = Guess(user_id=guest.id, peak_id=pg["peak_id"], is_correct=pg["is_correct"])
                db.add(guess)
                db.flush()
                session.setdefault("guess_ids", []).append(guess.id)

            game = Game(
                user_id=guest.id,
                score=body.score,
                correct_count=session.get("correct_count", 0),
                wrong_count=session.get("wrong_count", 0),
            )
            db.add(game)
            db.flush()
            if session.get("guess_ids"):
                db.query(Guess).filter(Guess.id.in_(session["guess_ids"])).update(
                    {"game_id": game.id}, synchronize_session=False
                )
        db.commit()

    rank = db.query(User).filter(User.best_score > body.score).count() + 1
    return {"rank": rank}
