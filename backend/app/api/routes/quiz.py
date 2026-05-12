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

# Cost in points deducted per hint type used on a question.
# Add new hint types here to extend the hint system.
HINT_COSTS: dict[str, int] = {
    "elevation": 25,
    "region": 25,
}

CATEGORY_ALL = "all"
CATEGORY_ALL_NAME = "Schweizer Berge"

# Special categories defined by elevation filter (id → display metadata)
SPECIAL_CATEGORIES: dict[str, dict] = {
    "4000m": {"name": "4000m Gipfel", "min_elevation": 4000},
}


def _streak_multiplier(streak: int) -> int:
    if streak < STREAK_THRESHOLD:
        return 1
    return min(streak - 1, STREAK_MAX_MULTIPLIER)


# In-memory session store (replace with Redis for production)
_sessions: dict[str, dict] = {}


def _select_picture(peak: Peak, exclude_pic_ids: set[int] | None = None) -> Picture | None:
    """Pick a random CDN picture for the peak, optionally skipping already-seen picture IDs."""
    cdn_pics = [p for p in peak.pictures if p.cdn_url]
    if exclude_pic_ids:
        cdn_pics = [p for p in cdn_pics if p.id not in exclude_pic_ids]
    return random.choice(cdn_pics) if cdn_pics else None


def _make_question(peak: Peak, distractor_pool: list[Peak], picture: Picture | None = None) -> QuizQuestion:
    distractors = random.sample([p for p in distractor_pool if p.id != peak.id], 3)
    options = [peak.name] + [d.name for d in distractors]
    random.shuffle(options)
    pic = picture if picture is not None else _select_picture(peak)
    image_url = ""
    if pic:
        cdn = (pic.cdn_url or "").replace("/upload/", "/upload/w_800,c_limit,f_auto,q_auto/", 1)
        image_url = cdn or pic.original_url or ""
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


def _eligible_peaks(db: Session, region: str | None = None, min_elevation: int | None = None) -> list[Peak]:
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
    if min_elevation is not None:
        q = q.filter(Peak.elevation >= min_elevation)
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

    # Special categories (elevation-filtered)
    for cat_id, meta in SPECIAL_CATEGORIES.items():
        special_peaks = _eligible_peaks(db, min_elevation=meta["min_elevation"])
        if special_peaks:
            highest_sp = max(special_peaks, key=lambda p: p.elevation or 0)
            highest_sp_pic = _select_picture(highest_sp)
            categories.append(
                CategoryResponse(
                    id=cat_id,
                    name=meta["name"],
                    peakCount=len(special_peaks),
                    imageUrl=(highest_sp_pic.cdn_url or "") if highest_sp_pic else "",
                )
            )

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
    mode = body.mode
    cat = body.category or CATEGORY_ALL
    special = SPECIAL_CATEGORIES.get(cat)
    region = None if (special or cat == CATEGORY_ALL) else cat
    min_elevation = special["min_elevation"] if special else None

    peaks = _eligible_peaks(db, region, min_elevation)
    if len(peaks) < 4:
        raise HTTPException(status_code=503, detail="Not enough peaks in database")

    selected = random.sample(peaks, min(INITIAL_BATCH, len(peaks)))
    seen_pic_ids: set[int] = set()
    questions = []
    for p in selected:
        pic = _select_picture(p)
        if pic:
            seen_pic_ids.add(pic.id)
        questions.append(_make_question(p, peaks, picture=pic))

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "answers": {q.id: q.peak.name for q in questions},
        "answered_question_ids": set(),
        "seen_pic_ids": seen_pic_ids,
        "score": 0,
        "correct_count": 0,
        "wrong_count": 0,
        "streak": 0,
        "pending_guesses": [],
        "category": cat,
        "region": region,
        "min_elevation": min_elevation,
        "mode": mode,
    }

    return QuizSession(sessionId=session_id, questions=questions, mode=mode)


@router.get("/next/{session_id}", response_model=QuizQuestion)
def next_question(session_id: str, db: Session = Depends(get_db)):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    region = session.get("region")
    min_elevation = session.get("min_elevation")
    peaks = _eligible_peaks(db, region, min_elevation)
    seen_pic_ids: set[int] = session["seen_pic_ids"]
    answered_ids: set[int] = session["answered_question_ids"]

    available = [
        p for p in peaks
        if p.id not in answered_ids
        and any(pic.id not in seen_pic_ids for pic in p.pictures if pic.cdn_url)
    ]
    if not available:
        raise HTTPException(status_code=404, detail="No more peaks available")

    peak = random.choice(available)
    pic = _select_picture(peak, exclude_pic_ids=seen_pic_ids)
    if pic:
        seen_pic_ids.add(pic.id)
    session["answers"][peak.id] = peak.name

    return _make_question(peak, peaks, picture=pic)


@router.post("/answer", response_model=AnswerResult)
def answer(body: AnswerRequest):
    session = _sessions.get(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if body.questionId in session["answered_question_ids"]:
        raise HTTPException(status_code=409, detail="Question already answered")

    correct_name = session["answers"].get(body.questionId)
    if correct_name is None:
        raise HTTPException(status_code=400, detail="Unknown question")

    session["answered_question_ids"].add(body.questionId)

    is_correct = body.answer.strip().lower() == correct_name.strip().lower()
    points_earned = 0
    if is_correct:
        session["streak"] += 1
        multiplier = _streak_multiplier(session["streak"])
        hint_penalty = sum(HINT_COSTS.get(h, 0) for h in body.hints_used)
        base = max(10, POINTS_PER_CORRECT - hint_penalty)
        points_earned = base * multiplier
        session["score"] += points_earned
        session["correct_count"] += 1
    else:
        session["streak"] = 0
        multiplier = 1
        session["wrong_count"] += 1

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
    game_mode = session.get("mode", "timed") if session else "timed"
    is_chill = game_mode == "chill"

    if current_user:
        if body.nickname:
            current_user.username = body.nickname
        if not is_chill and body.score > current_user.best_score:
            current_user.best_score = body.score

        if session:
            guess_ids = []
            for pg in session.get("pending_guesses", []):
                guess = Guess(user_id=current_user.id, peak_id=pg["peak_id"], is_correct=pg["is_correct"])
                db.add(guess)
                db.flush()
                guess_ids.append(guess.id)

            game = Game(
                user_id=current_user.id,
                score=body.score,
                correct_count=session.get("correct_count", 0),
                wrong_count=session.get("wrong_count", 0),
                category=category,
                mode=game_mode,
            )
            db.add(game)
            db.flush()
            if guess_ids:
                db.query(Guess).filter(Guess.id.in_(guess_ids)).update(
                    {"game_id": game.id}, synchronize_session=False
                )
        db.commit()
    elif body.guestId:
        guest = db.get(User, body.guestId)
        if not guest:
            initial_best = body.score if not is_chill else 0
            guest = User(id=body.guestId, username=body.nickname or body.guestId, best_score=initial_best)
            db.add(guest)
            db.flush()
        else:
            if body.nickname:
                guest.username = body.nickname
            if not is_chill and body.score > guest.best_score:
                guest.best_score = body.score

        if session:
            guess_ids = []
            for pg in session.get("pending_guesses", []):
                guess = Guess(user_id=guest.id, peak_id=pg["peak_id"], is_correct=pg["is_correct"])
                db.add(guess)
                db.flush()
                guess_ids.append(guess.id)

            game = Game(
                user_id=guest.id,
                score=body.score,
                correct_count=session.get("correct_count", 0),
                wrong_count=session.get("wrong_count", 0),
                category=category,
                mode=game_mode,
            )
            db.add(game)
            db.flush()
            if guess_ids:
                db.query(Guess).filter(Guess.id.in_(guess_ids)).update(
                    {"game_id": game.id}, synchronize_session=False
                )
        db.commit()

    if is_chill:
        return {"rank": 0}
    rank = db.query(User).filter(User.best_score > body.score).count() + 1
    return {"rank": rank}
