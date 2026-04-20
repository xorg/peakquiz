from datetime import datetime

from pydantic import BaseModel


class TroublePeakOut(BaseModel):
    peakId: int
    peakName: str
    imageUrl: str
    wrongCount: int
    totalAttempts: int


class FavouritePeakOut(BaseModel):
    peakId: int
    peakName: str
    imageUrl: str
    correctCount: int
    totalAttempts: int


class GameOut(BaseModel):
    id: int
    score: int
    correctCount: int
    wrongCount: int
    playedAt: datetime


class ProfileStats(BaseModel):
    userId: str
    username: str
    isGuest: bool
    totalGuesses: int
    correctGuesses: int
    accuracyPercent: float
    troublePeaks: list[TroublePeakOut]
    favouritePeaks: list[FavouritePeakOut]
    recentGames: list[GameOut]


class NicknameUpdate(BaseModel):
    nickname: str
    guestId: str | None = None
