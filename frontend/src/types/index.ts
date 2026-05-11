export interface Peak {
  id: number
  name: string
  imageUrl: string
  heightM: number
  country: string
  authorName?: string
  authorUrl?: string
  licenseName?: string
  licenseUrl?: string
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
  mode: string
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
  is_admin?: boolean
}

export interface TroublePeak {
  peakId: number
  peakName: string
  imageUrl: string
  wrongCount: number
  totalAttempts: number
}

export interface FavouritePeak {
  peakId: number
  peakName: string
  imageUrl: string
  correctCount: number
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
  userId: string
  username: string
  isGuest: boolean
  totalGuesses: number
  correctGuesses: number
  accuracyPercent: number
  troublePeaks: TroublePeak[]
  favouritePeaks: FavouritePeak[]
  recentGames: GameEntry[]
}

export interface AnswerRecord {
  peak: Peak
  wasCorrect: boolean
}

export interface Category {
  id: string
  name: string
  peakCount: number
  imageUrl: string
}

export type QuizState = 'idle' | 'active' | 'nickname' | 'finished'

export type AnswerState = 'unanswered' | 'correct' | 'wrong'

// Admin types
export interface AdminPeak {
  id: number
  name: string
  region: string | null
  elevation: number | null
  picture_count: number
}

export interface AdminPicture {
  id: number
  cdn_url: string | null
  original_url: string
  title: string | null
  author_name: string | null
  author_url: string | null
  license_name: string | null
  license_url: string | null
  source: string | null
}

export interface AdminPeakDetail {
  id: number
  name: string
  region: string | null
  elevation: number | null
  mountain_range: string | null
  peak_type: string | null
  pictures: AdminPicture[]
}

export interface WikiSearchResult {
  filename: string
  title: string
  direct_url: string
  source: string
  author_name: string | null
  author_url: string | null
  license_name: string | null
  license_url: string | null
}
