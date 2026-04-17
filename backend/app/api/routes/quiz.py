import random
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ...db.database import get_db
from ...db.models import Peak, Picture, User
from ...schemas.quiz import AnswerRequest, AnswerResult, FinishRequest, QuizSession, QuizQuestion, PeakOut
from ...api.routes.auth import get_optional_user

router = APIRouter(prefix="/quiz", tags=["quiz"])

POINTS_PER_CORRECT = 100
INITIAL_BATCH = 10

# In-memory session store (replace with Redis for production)
_sessions: dict[str, dict] = {}


def _best_image(peak: Peak) -> str | None:
    for pic in peak.pictures:
        if pic.cdn_url:
            # Inject resize transform before the public ID; w_800,c_limit caps delivery width without upscaling
            return pic.cdn_url.replace("/upload/", "/upload/w_800,c_limit/", 1)
    for pic in peak.pictures:
        if pic.original_url:
            return pic.original_url
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
            imageUrl=_best_image(peak) or "",
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
def answer(body: AnswerRequest):
    session = _sessions.get(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    correct_name = session["answers"].get(body.questionId)
    if correct_name is None:
        raise HTTPException(status_code=400, detail="Unknown question")

    is_correct = body.answer.strip().lower() == correct_name.strip().lower()
    if is_correct:
        session["score"] += POINTS_PER_CORRECT

    return AnswerResult(
        correct=is_correct,
        pointsEarned=POINTS_PER_CORRECT if is_correct else 0,
        totalPoints=session["score"],
    )


@router.post("/finish")
def finish_quiz(
    body: FinishRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    _sessions.pop(body.sessionId, None)

    if current_user:
        if body.score > current_user.best_score:
            current_user.best_score = body.score
            db.commit()
    elif body.nickname and body.guestId:
        guest = db.get(User, body.guestId)
        if not guest:
            guest = User(id=body.guest_id, username=body.nickname, best_score=body.score)
            db.add(guest)
        else:
            guest.username = body.nickname
            if body.score > guest.best_score:
                guest.best_score = body.score
        db.commit()

    rank = db.query(User).filter(User.best_score > body.score).count() + 1
    return {"rank": rank}
