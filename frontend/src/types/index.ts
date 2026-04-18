export interface Peak {
  id: number
  name: string
  imageUrl: string
  heightM: number
  country: string
}

export interface QuizQuestion {
  id: number
  peak: Peak
  options: string[]
}

export interface QuizSession {
  sessionId: string
  questions: QuizQuestion[]
  durationSeconds: number
}

export interface AnswerResult {
  correct: boolean
  pointsEarned: number
  totalPoints: number
  streak: number
  multiplier: number
}

export interface RankingEntry {
  rank: number
  username: string
  score: number
  isCurrentUser?: boolean
}

export interface User {
  id: string
  username: string
  email: string
  avatarUrl?: string
}

export interface TroublePeak {
  peakId: number
  peakName: string
  imageUrl: string
  wrongCount: number
  totalAttempts: number
}

export interface GameEntry {
  id: number
  score: number
  correctCount: number
  wrongCount: number
  playedAt: string
}

export interface ProfileStats {
  totalGuesses: number
  correctGuesses: number
  accuracyPercent: number
  troublePeaks: TroublePeak[]
  recentGames: GameEntry[]
}

export interface AnswerRecord {
  peak: Peak
  wasCorrect: boolean
}

export type QuizState = 'idle' | 'active' | 'nickname' | 'finished'

export type AnswerState = 'unanswered' | 'correct' | 'wrong'
