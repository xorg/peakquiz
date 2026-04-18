import type { QuizSession, QuizQuestion, AnswerResult, RankingEntry, User, ProfileStats } from '../types'

const BASE_URL = import.meta.env.VITE_BACKEND_HOST
  ? `https://${import.meta.env.VITE_BACKEND_HOST}/api`
  : '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    ...init,
  })
  if (!res.ok) {
    const error = await res.text()
    throw new Error(error || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  auth: {
    me: () => request<User>('/auth/me'),
    logout: () => request<void>('/auth/logout', { method: 'POST' }),
    googleLoginUrl: () => `${BASE_URL}/auth/google/login`,
  },

  quiz: {
    start: () => request<QuizSession>('/quiz/start', { method: 'POST' }),
    answer: (sessionId: string, questionId: number, answer: string) =>
      request<AnswerResult>('/quiz/answer', {
        method: 'POST',
        body: JSON.stringify({ sessionId, questionId, answer }),
      }),
    next: (sessionId: string) =>
      request<QuizQuestion>(`/quiz/next/${sessionId}`),
    finish: (sessionId: string, score: number, nickname?: string, guestId?: string) =>
      request<{ rank: number }>('/quiz/finish', {
        method: 'POST',
        body: JSON.stringify({ sessionId, score, nickname, guestId }),
      }),
  },

  rankings: {
    global: (limit = 50) => request<RankingEntry[]>(`/rankings?limit=${limit}`),
  },

  profile: {
    stats: () => request<ProfileStats>('/profile/stats'),
  },
}
