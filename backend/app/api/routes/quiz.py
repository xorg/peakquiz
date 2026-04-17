import random
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ...db.database import get_db
from ...db.models import Peak, Picture, User
from ...schemas.quiz import AnswerRequest, AnswerResult, FinishRequest, QuizSession, QuizQuestion, PeakOut
from ...api.routes.auth import get_current_user

router = APIRouter(prefix="/quiz", tags=["quiz"])

POINTS_PER_CORRECT = 100
QUIZ_SIZE = 10

# In-memory session store (replace with Redis for production)
_sessions: dict[str, dict] = {}


def _best_image(peak: Peak) -> str | None:
    for pic in peak.pictures:
        if pic.cdn_url:
            return pic.cdn_url
    for pic in peak.pictures:
        if pic.original_url:
            return pic.original_url
    return None


@router.post("/start", response_model=QuizSession)
def start_quiz(db: Session = Depends(get_db)):
    peaks = (
        db.query(Peak)
        .join(Picture)
        .filter(Picture.cdn_url.isnot(None))
        .options(joinedload(Peak.pictures))
        .distinct()
        .all()
    )
    if len(peaks) < 4:
        raise HTTPException(status_code=503, detail="Not enough peaks in database")

    selected = random.sample(peaks, min(QUIZ_SIZE, len(peaks)))
    questions = []
    for peak in selected:
        distractors = random.sample([p for p in peaks if p.id != peak.id], 3)
        options = [peak.name] + [d.name for d in distractors]
        random.shuffle(options)
        questions.append(QuizQuestion(
            id=peak.id,
            peak=PeakOut(
                id=peak.id,
                name=peak.name,
                imageUrl=_best_image(peak) or "",
                heightM=peak.elevation or 0,
                country=peak.region or "",
            ),
            options=options,
        ))

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "questions": {q.id: q.peak.name for q in questions},
        "score": 0,
    }

    return QuizSession(sessionId=session_id, questions=questions)


@router.post("/answer", response_model=AnswerResult)
def answer(body: AnswerRequest):
    session = _sessions.get(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    correct_name = session["questions"].get(body.questionId)
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
    current_user: User | None = Depends(lambda r=None: None),
):
    _sessions.pop(body.sessionId, None)

    if current_user and body.score > current_user.best_score:
        current_user.best_score = body.score
        db.commit()

    rank = db.query(User).filter(User.best_score > body.score).count() + 1
    return {"rank": rank}
