from pydantic import BaseModel


class PeakOut(BaseModel):
    id: int
    name: str
    imageUrl: str
    heightM: int
    country: str


class QuizQuestion(BaseModel):
    id: int
    peak: PeakOut
    options: list[str]


class QuizSession(BaseModel):
    sessionId: str
    questions: list[QuizQuestion]
    durationSeconds: int = 60


class AnswerRequest(BaseModel):
    sessionId: str
    questionId: int
    answer: str


class AnswerResult(BaseModel):
    correct: bool
    pointsEarned: int
    totalPoints: int


class FinishRequest(BaseModel):
    sessionId: str
    score: int


class RankingEntry(BaseModel):
    rank: int
    username: str
    score: int
