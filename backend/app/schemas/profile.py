from pydantic import BaseModel


class TroublePeakOut(BaseModel):
    peakId: int
    peakName: str
    imageUrl: str
    wrongCount: int
    totalAttempts: int


class ProfileStats(BaseModel):
    totalGuesses: int
    correctGuesses: int
    accuracyPercent: float
    troublePeaks: list[TroublePeakOut]
