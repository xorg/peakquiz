import random
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ...api.routes.auth import get_optional_user
from ...db.database import get_db
from ...db.models import Game, Guess, Peak, Picture, User
from ...schemas.quiz import (
    AnswerRequest,
    AnswerResult,
    CategoryResponse,
    FinishRequest,
    PeakOut,
    QuizQuestion,
    QuizSession,
    StartRequest,
)

router = APIRouter(prefix="/quiz", tags=["quiz"])

POINTS_PER_CORRECT = 100
INITIAL_BATCH = 10
STREAK_THRESHOLD = 3
STREAK_MAX_MULTIPLIER = 4

CATEGORY_ALL = "all"
CATEGORY_ALL_NAME = "Schweizer Berge"


def _streak_multiplier(streak: int) -> int:
    if streak < STREAK_THRESHOLD:
        return 1
    return min(streak - 1, STREAK_MAX_MULTIPLIER)


# In-memory session store (replace with Redis for production)
_sessions: dict[str, dict] = {}


def _select_picture(peak: Peak) -> Picture | None:
    """Pick a random picture for the peak, preferring CDN images."""
    cdn_pics = [p for p in peak.pictures if p.cdn_url]
    if cdn_pics:
        return random.choice(cdn_pics)
    any_pics = [p for p in peak.pictures if p.original_url]
    return random.choice(any_pics) if any_pics else None


def _make_question(peak: Peak, distractor_pool: list[Peak]) -> QuizQuestion:
    distractors = random.sample([p for p in distractor_pool if p.id != peak.id], 3)
    options = [peak.name] + [d.name for d in distractors]
    random.shuffle(options)
    pic = _select_picture(peak)
    image_url = ""
    if pic:
        image_url = (pic.cdn_url or "").replace("/upload/", "/upload/w_800,c_limit/", 1) or pic.original_url or ""
    return QuizQuestion(
        id=peak.id,
        peak=PeakOut(
            id=peak.id,
            name=peak.name,
            imageUrl=image_url,
            heightM=peak.elevation or 0,
            country=peak.region or "",
            authorName=pic.author_rel.name if pic and pic.author_rel else None,
            authorUrl=pic.author_rel.url if pic and pic.author_rel else None,
            licenseName=pic.license_rel.name if pic and pic.license_rel else None,
            licenseUrl=pic.license_rel.url if pic and pic.license_rel else None,
        ),
        options=options,
    )


def _eligible_peaks(db: Session, region: str | None = None) -> list[Peak]:
    q = (
        db.query(Peak)
        .join(Picture)
        .filter(Picture.cdn_url.isnot(None))
        .options(
            joinedload(Peak.pictures).joinedload(Picture.author_rel),
            joinedload(Peak.pictures).joinedload(Picture.license_rel),
        )
        .distinct()
    )
    if region:
        q = q.filter(Peak.region == region)
    return q.all()


@router.get("/categories", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    all_peaks = _eligible_peaks(db)

    # Overall "Schweizer Berge" category — highest peak overall
    overall_peak = max(all_peaks, key=lambda p: p.elevation or 0) if all_peaks else None
    overall_pic = _select_picture(overall_peak) if overall_peak else None
    categories: list[CategoryResponse] = [
        CategoryResponse(
            id=CATEGORY_ALL,
            name=CATEGORY_ALL_NAME,
            peakCount=len(all_peaks),
            imageUrl=(overall_pic.cdn_url or "") if overall_pic else "",
        )
    ]

    # One entry per region
    regions: dict[str, list[Peak]] = {}
    for peak in all_peaks:
        if peak.region:
            regions.setdefault(peak.region, []).append(peak)

    for region, peaks in sorted(regions.items()):
        highest = max(peaks, key=lambda p: p.elevation or 0)
        highest_pic = _select_picture(highest)
        categories.append(
            CategoryResponse(
                id=region,
                name=region,
                peakCount=len(peaks),
                imageUrl=(highest_pic.cdn_url or "") if highest_pic else "",
            )
        )

    return categories


@router.post("/start", response_model=QuizSession)
def start_quiz(body: StartRequest = StartRequest(), db: Session = Depends(get_db)):
    region = None if (body.category is None or body.category == CATEGORY_ALL) else body.category

    peaks = _eligible_peaks(db, region)
    if len(peaks) < 4:
        raise HTTPException(status_code=503, detail="Not enough peaks in database")

    # Distractors come from the same regional pool
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
        "pending_guesses": [],
        "category": body.category or CATEGORY_ALL,
        "region": region,
    }

    return QuizSession(sessionId=session_id, questions=questions)


@router.get("/next/{session_id}", response_model=QuizQuestion)
def next_question(session_id: str, db: Session = Depends(get_db)):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    region = session.get("region")
    peaks = _eligible_peaks(db, region)
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
    category = session.get("category", CATEGORY_ALL) if session else CATEGORY_ALL

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
                category=category,
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
                category=category,
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
