from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import User
from ...schemas.quiz import RankingEntry

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("", response_model=list[RankingEntry])
def get_rankings(limit: int = Query(default=50, le=100), db: Session = Depends(get_db)):
    users = (
        db.query(User)
        .filter(User.best_score > 0)
        .order_by(User.best_score.desc())
        .limit(limit)
        .all()
    )
    return [
        RankingEntry(rank=i + 1, username=u.username, score=u.best_score)
        for i, u in enumerate(users)
    ]
