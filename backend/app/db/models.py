from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Google sub
    username: Mapped[str] = mapped_column(String, nullable=False)
    best_score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    guesses: Mapped[list["Guess"]] = relationship("Guess", back_populates="user")
    games: Mapped[list["Game"]] = relationship(
        "Game", back_populates="user", order_by="Game.created_at.desc()"
    )


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="games")
    guesses: Mapped[list["Guess"]] = relationship("Guess", back_populates="game")


class Guess(Base):
    __tablename__ = "guesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    peak_id: Mapped[int] = mapped_column(Integer, ForeignKey("peaks.id"), nullable=False, index=True)
    game_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("games.id"), nullable=True, index=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="guesses")
    peak: Mapped["Peak"] = relationship("Peak")
    game: Mapped["Game | None"] = relationship("Game", back_populates="guesses")


class Peak(Base):
    __tablename__ = "peaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    aliases: Mapped[str | None] = mapped_column(String, nullable=True)
    dominance_peak: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dominance_distance: Mapped[float | None] = mapped_column(Float, nullable=True)
    prominence_distance: Mapped[float | None] = mapped_column(Float, nullable=True)
    prominence_peak: Mapped[str | None] = mapped_column(String(255), nullable=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    elevation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mountain_range: Mapped[str | None] = mapped_column(String(255), nullable=True)
    peak_type: Mapped[str | None] = mapped_column(String(255), nullable=True)

    pictures: Mapped[list["Picture"]] = relationship("Picture", back_populates="peak")


class Picture(Base):
    __tablename__ = "pictures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    peak_id: Mapped[int] = mapped_column(Integer, ForeignKey("peaks.id"), nullable=False)
    original_url: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cdn_url: Mapped[str | None] = mapped_column(String(200), nullable=True, unique=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cdn_asset_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    peak: Mapped["Peak"] = relationship("Peak", back_populates="pictures")
