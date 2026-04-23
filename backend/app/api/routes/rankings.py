from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import Game, User
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


@router.get("/category/{category}", response_model=list[RankingEntry])
def get_category_rankings(
    category: str,
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db),
):
    from ...api.routes.quiz import CATEGORY_ALL  # avoid circular at module level

    cat_filter = (
        (Game.category == category) | Game.category.is_(None)
        if category == CATEGORY_ALL
        else Game.category == category
    )
    rows = (
        db.query(User.username, func.max(Game.score).label("best"))
        .join(Game, Game.user_id == User.id)
        .filter(cat_filter)
        .group_by(User.id)
        .order_by(func.max(Game.score).desc())
        .limit(limit)
        .all()
    )
    return [
        RankingEntry(rank=i + 1, username=row.username, score=row.best)
        for i, row in enumerate(rows)
    ]
