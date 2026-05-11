import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '../services/api'
import type { QuizQuestion, AnswerState, QuizState, AnswerRecord } from '../types'

const QUIZ_DURATION_SECONDS = 60
const MAX_WRONG_TIMED = 5
const MAX_WRONG_CHILL = 3

function getOrCreateGuestId(): string {
  const key = 'pq_guest_id'
  let id = localStorage.getItem(key)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(key, id)
  }
  return id
}

const BONUS_THRESHOLD_SECONDS = 10
const BONUS_SECONDS = 5

export type QuizMode = 'timed' | 'chill'

export function useQuiz() {
  const [quizState, setQuizState] = useState<QuizState>('idle')
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [score, setScore] = useState(0)
  const [timeLeft, setTimeLeft] = useState(QUIZ_DURATION_SECONDS)
  const [answerState, setAnswerState] = useState<AnswerState>('unanswered')
  const [wrongOption, setWrongOption] = useState<string | null>(null)
  const [correctOption, setCorrectOption] = useState<string | null>(null)
  const [lastPoints, setLastPoints] = useState(0)
  const [wrongCount, setWrongCount] = useState(0)
  const [answerHistory, setAnswerHistory] = useState<AnswerRecord[]>([])
  const [streak, setStreak] = useState(0)
  const [multiplier, setMultiplier] = useState(1)
  const [mode, setMode] = useState<QuizMode>('timed')
  // Set of hint type strings revealed for the current question (e.g. 'elevation', 'region')
  const [hintsRevealed, setHintsRevealed] = useState<Set<string>>(new Set())

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const finishTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isEndingRef = useRef(false)
  const sessionIdRef = useRef<string | null>(null)
  const scoreRef = useRef(0)
  const questionsRef = useRef<QuizQuestion[]>([])
  const currentIndexRef = useRef(0)
  const modeRef = useRef<QuizMode>('timed')

  scoreRef.current = score
  questionsRef.current = questions
  currentIndexRef.current = currentIndex
  modeRef.current = mode

  const currentQuestion = questions[currentIndex] ?? null
  const maxWrong = mode === 'chill' ? MAX_WRONG_CHILL : MAX_WRONG_TIMED

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const finishQuiz = useCallback(() => {
    if (isEndingRef.current) return
    isEndingRef.current = true
    if (finishTimeoutRef.current) {
      clearTimeout(finishTimeoutRef.current)
      finishTimeoutRef.current = null
    }
    stopTimer()
    setQuizState('nickname')
  }, [stopTimer])

  const submitNickname = useCallback(async (nickname: string) => {
    const sid = sessionIdRef.current
    if (sid) {
      const guestId = getOrCreateGuestId()
      try {
        await api.quiz.finish(sid, scoreRef.current, nickname || undefined, nickname ? guestId : undefined)
      } catch { /* show local score regardless */ }
    }
    setQuizState('finished')
  }, [])

  const advance = useCallback(async () => {
    const nextIndex = currentIndexRef.current + 1
    setAnswerState('unanswered')
    setWrongOption(null)
    setCorrectOption(null)
    setLastPoints(0)
    setHintsRevealed(new Set())

    if (nextIndex < questionsRef.current.length) {
      setCurrentIndex(nextIndex)
      return
    }

    try {
      const nextQ = await api.quiz.next(sessionIdRef.current!)
      setQuestions(prev => [...prev, nextQ])
      setCurrentIndex(nextIndex)
    } catch {
      finishQuiz()
    }
  }, [finishQuiz])

  const startQuiz = async (category?: string, quizMode: QuizMode = 'timed') => {
    stopTimer()
    isEndingRef.current = false
    setScore(0)
    scoreRef.current = 0
    setCurrentIndex(0)
    currentIndexRef.current = 0
    setQuestions([])
    questionsRef.current = []
    setAnswerState('unanswered')
    setWrongOption(null)
    setWrongCount(0)
    setAnswerHistory([])
    setStreak(0)
    setMultiplier(1)
    setMode(quizMode)
    modeRef.current = quizMode
    setHintsRevealed(new Set())
    setTimeLeft(QUIZ_DURATION_SECONDS)

    const newSession = await api.quiz.start(category, quizMode)
    sessionIdRef.current = newSession.sessionId
    setQuestions(newSession.questions)
    questionsRef.current = newSession.questions
    setQuizState('active')

    if (quizMode === 'timed') {
      timerRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            finishQuiz()
            return 0
          }
          return prev - 1
        })
      }, 1000)
    }
  }

  const revealHint = useCallback((hintType: string) => {
    setHintsRevealed(prev => {
      if (prev.has(hintType)) return prev
      const next = new Set(prev)
      next.add(hintType)
      return next
    })
  }, [])

  const submitAnswer = async (answer: string) => {
    if (!currentQuestion || answerState !== 'unanswered') return

    const hintsUsed = [...hintsRevealed]
    const result = await api.quiz.answer(sessionIdRef.current!, currentQuestion.id, answer, hintsUsed)

    setAnswerHistory(prev => [...prev, { peak: currentQuestion.peak, wasCorrect: result.correct }])
    setStreak(result.streak)
    setMultiplier(result.multiplier)

    if (result.correct) {
      const newScore = result.totalPoints
      setScore(newScore)
      scoreRef.current = newScore
      setCorrectOption(answer)
      setLastPoints(result.pointsEarned)
      setAnswerState('correct')
      if (modeRef.current === 'timed' && timeLeft <= BONUS_THRESHOLD_SECONDS) {
        setTimeLeft(prev => prev + BONUS_SECONDS)
      }
      setTimeout(() => advance(), 600)
    } else {
      setWrongOption(answer)
      setAnswerState('wrong')
      const nextWrong = wrongCount + 1
      setWrongCount(nextWrong)
      const limit = modeRef.current === 'chill' ? MAX_WRONG_CHILL : MAX_WRONG_TIMED
      if (nextWrong >= limit) {
        finishTimeoutRef.current = setTimeout(() => finishQuiz(), 900)
      } else {
        setTimeout(() => advance(), 900)
      }
    }
  }

  useEffect(() => {
    questions.forEach(q => {
      if (q.peak.imageUrl) new Image().src = q.peak.imageUrl
    })
  }, [questions])

  useEffect(() => () => stopTimer(), [stopTimer])

  return {
    quizState,
    currentQuestion,
    score,
    timeLeft,
    answerState,
    wrongOption,
    correctOption,
    lastPoints,
    startQuiz,
    submitAnswer,
    submitNickname,
    answeredCount: currentIndex,
    wrongCount,
    maxWrong,
    answerHistory,
    streak,
    multiplier,
    mode,
    hintsRevealed,
    revealHint,
  }
}
