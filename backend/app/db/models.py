from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Google sub
    username: Mapped[str] = mapped_column(String, nullable=False)
    best_score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


class Peak(Base):
    __tablename__ = "peaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    image_url: Mapped[str] = mapped_column(String, nullable=False)
    height_m: Mapped[int] = mapped_column(Integer, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
