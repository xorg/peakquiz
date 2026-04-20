from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ...api.routes.auth import get_optional_user
from ...db.database import get_db
from ...db.models import Game, Guess, Peak, User
from ...schemas.profile import (
    FavouritePeakOut,
    GameOut,
    NicknameUpdate,
    ProfileStats,
    TroublePeakOut,
)

router = APIRouter(prefix="/profile", tags=["profile"])


def _resolve_user(
    db: Session,
    current_user: User | None,
    guest_id: str | None,
) -> tuple[User, bool]:
    """Return (user, is_guest). Prefers the authenticated user; falls back to guest lookup."""
    if current_user:
        return current_user, False
    if guest_id:
        guest = db.get(User, guest_id)
        if guest:
            return guest, True
    raise HTTPException(status_code=404, detail="Profile not found")


def _image_url(peak: Peak) -> str:
    for pic in peak.pictures:
        if pic.cdn_url:
            return pic.cdn_url.replace("/upload/", "/upload/w_400,c_limit/", 1)
    for pic in peak.pictures:
        if pic.original_url:
            return pic.original_url
    return ""


@router.get("/stats", response_model=ProfileStats)
def get_stats(
    guestId: str | None = None,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    user, is_guest = _resolve_user(db, current_user, guestId)
    # Count of all guess rows for this user, regardless of outcome
    total = db.query(func.count(Guess.id)).filter(Guess.user_id == user.id).scalar() or 0

    # Count of guess rows where the user answered correctly
    correct = (
        db.query(func.count(Guess.id))
        .filter(Guess.user_id == user.id, Guess.is_correct.is_(True))
        .scalar() or 0
    )

    # Per-peak wrong-guess counts for this user; only peaks with ≥ 2 wrong answers
    # qualify, ordered worst-first and capped at 5 — used as the subquery source for
    # the trouble-peaks join below
    wrong_subq = (
        db.query(Guess.peak_id, func.count(Guess.id).label("wrong_count"))
        .filter(Guess.user_id == user.id, Guess.is_correct.is_(False))
        .group_by(Guess.peak_id)
        .having(func.count(Guess.id) >= 2)
        .order_by(func.count(Guess.id).desc())
        .limit(5)
        .subquery()
    )

    # Join Peak rows to the subquery to get full peak data alongside wrong_count
    trouble_rows = (
        db.query(Peak, wrong_subq.c.wrong_count)
        .join(wrong_subq, Peak.id == wrong_subq.c.peak_id)
        .options(joinedload(Peak.pictures))
        .all()
    )

    trouble_peaks = []
    for peak, wrong_count in trouble_rows:
        # Total guesses (right + wrong) for this specific peak, used to show accuracy context
        total_attempts = (
            db.query(func.count(Guess.id))
            .filter(Guess.user_id == user.id, Guess.peak_id == peak.id)
            .scalar() or 0
        )
        trouble_peaks.append(TroublePeakOut(
            peakId=peak.id,
            peakName=peak.name,
            imageUrl=_image_url(peak),
            wrongCount=wrong_count,
            totalAttempts=total_attempts,
        ))

    correct_subq = (
        db.query(Guess.peak_id, func.count(Guess.id).label("correct_count"))
        .filter(Guess.user_id == user.id, Guess.is_correct.is_(True))
        .group_by(Guess.peak_id)
        .having(func.count(Guess.id) >= 2)
        .order_by(func.count(Guess.id).desc())
        .limit(5)
        .subquery()
    )

    favourite_rows = (
        db.query(Peak, correct_subq.c.correct_count)
        .join(correct_subq, Peak.id == correct_subq.c.peak_id)
        .options(joinedload(Peak.pictures))
        .all()
    )

    favourite_peaks = []
    for peak, correct_count in favourite_rows:
        total_attempts = (
            db.query(func.count(Guess.id))
            .filter(Guess.user_id == user.id, Guess.peak_id == peak.id)
            .scalar() or 0
        )
        favourite_peaks.append(FavouritePeakOut(
            peakId=peak.id,
            peakName=peak.name,
            imageUrl=_image_url(peak),
            correctCount=correct_count,
            totalAttempts=total_attempts,
        ))

    # Last 10 completed games for this user, newest first
    recent_game_rows = (
        db.query(Game)
        .filter(Game.user_id == user.id)
        .order_by(Game.created_at.desc())
        .limit(10)
        .all()
    )
    recent_games = [
        GameOut(
            id=g.id,
            score=g.score,
            correctCount=g.correct_count,
            wrongCount=g.wrong_count,
            playedAt=g.created_at,
        )
        for g in recent_game_rows
    ]

    return ProfileStats(
        userId=user.id,
        username=user.username,
        isGuest=is_guest,
        totalGuesses=total,
        correctGuesses=correct,
        accuracyPercent=round(correct / total * 100, 1) if total > 0 else 0.0,
        troublePeaks=trouble_peaks,
        favouritePeaks=favourite_peaks,
        recentGames=recent_games,
    )


@router.patch("/nickname")
def update_nickname(
    body: NicknameUpdate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    user, _ = _resolve_user(db, current_user, body.guestId)
    name = body.nickname.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nickname cannot be empty")
    user.username = name
    db.commit()
    return {"username": user.username}
