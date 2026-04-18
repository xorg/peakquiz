from datetime import datetime
from pydantic import BaseModel


class TroublePeakOut(BaseModel):
    peakId: int
    peakName: str
    imageUrl: str
    wrongCount: int
    totalAttempts: int


class GameOut(BaseModel):
    id: int
    score: int
    correctCount: int
    wrongCount: int
    playedAt: datetime


class ProfileStats(BaseModel):
    totalGuesses: int
    correctGuesses: int
    accuracyPercent: float
    troublePeaks: list[TroublePeakOut]
    recentGames: list[GameOut]
