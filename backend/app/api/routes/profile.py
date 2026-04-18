from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ...db.database import get_db
from ...db.models import Guess, Peak, User
from ...schemas.profile import ProfileStats, TroublePeakOut
from ...api.routes.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])


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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = db.query(func.count(Guess.id)).filter(Guess.user_id == current_user.id).scalar() or 0
    correct = (
        db.query(func.count(Guess.id))
        .filter(Guess.user_id == current_user.id, Guess.is_correct.is_(True))
        .scalar() or 0
    )

    wrong_subq = (
        db.query(Guess.peak_id, func.count(Guess.id).label("wrong_count"))
        .filter(Guess.user_id == current_user.id, Guess.is_correct.is_(False))
        .group_by(Guess.peak_id)
        .having(func.count(Guess.id) >= 2)
        .order_by(func.count(Guess.id).desc())
        .limit(5)
        .subquery()
    )

    trouble_rows = (
        db.query(Peak, wrong_subq.c.wrong_count)
        .join(wrong_subq, Peak.id == wrong_subq.c.peak_id)
        .options(joinedload(Peak.pictures))
        .all()
    )

    trouble_peaks = []
    for peak, wrong_count in trouble_rows:
        total_attempts = (
            db.query(func.count(Guess.id))
            .filter(Guess.user_id == current_user.id, Guess.peak_id == peak.id)
            .scalar() or 0
        )
        trouble_peaks.append(TroublePeakOut(
            peakId=peak.id,
            peakName=peak.name,
            imageUrl=_image_url(peak),
            wrongCount=wrong_count,
            totalAttempts=total_attempts,
        ))

    return ProfileStats(
        totalGuesses=total,
        correctGuesses=correct,
        accuracyPercent=round(correct / total * 100, 1) if total > 0 else 0.0,
        troublePeaks=trouble_peaks,
    )
