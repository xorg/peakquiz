import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '../services/api'
import type { QuizQuestion, AnswerState, QuizState } from '../types'

const QUIZ_DURATION_SECONDS = 60
const BONUS_THRESHOLD_SECONDS = 10
const BONUS_SECONDS = 5

export function useQuiz() {
  const [quizState, setQuizState] = useState<QuizState>('idle')
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [score, setScore] = useState(0)
  const [timeLeft, setTimeLeft] = useState(QUIZ_DURATION_SECONDS)
  const [answerState, setAnswerState] = useState<AnswerState>('unanswered')
  const [wrongOption, setWrongOption] = useState<string | null>(null)

  // Refs so timer and async callbacks always see current values
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const sessionIdRef = useRef<string | null>(null)
  const scoreRef = useRef(0)
  const questionsRef = useRef<QuizQuestion[]>([])
  const currentIndexRef = useRef(0)

  scoreRef.current = score
  questionsRef.current = questions
  currentIndexRef.current = currentIndex

  const currentQuestion = questions[currentIndex] ?? null

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const finishQuiz = useCallback(async (finalScore: number) => {
    stopTimer()
    setQuizState('finished')
    const sid = sessionIdRef.current
    if (sid) {
      try { await api.quiz.finish(sid, finalScore) } catch { /* show local score regardless */ }
    }
  }, [stopTimer])

  const advance = useCallback(async () => {
    const nextIndex = currentIndexRef.current + 1
    setAnswerState('unanswered')
    setWrongOption(null)

    if (nextIndex < questionsRef.current.length) {
      setCurrentIndex(nextIndex)
      return
    }

    // Fetch the next unseen question from the backend
    try {
      const nextQ = await api.quiz.next(sessionIdRef.current!)
      setQuestions(prev => [...prev, nextQ])
      setCurrentIndex(nextIndex)
    } catch {
      // All peaks exhausted or session gone — end the quiz
      finishQuiz(scoreRef.current)
    }
  }, [finishQuiz])

  const startQuiz = async () => {
    stopTimer()
    setScore(0)
    scoreRef.current = 0
    setCurrentIndex(0)
    currentIndexRef.current = 0
    setQuestions([])
    questionsRef.current = []
    setAnswerState('unanswered')
    setWrongOption(null)
    setTimeLeft(QUIZ_DURATION_SECONDS)

    const newSession = await api.quiz.start()
    sessionIdRef.current = newSession.sessionId
    setQuestions(newSession.questions)
    questionsRef.current = newSession.questions
    setQuizState('active')

    timerRef.current = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          finishQuiz(scoreRef.current)
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }

  const submitAnswer = async (answer: string) => {
    if (!currentQuestion || answerState !== 'unanswered') return

    const result = await api.quiz.answer(sessionIdRef.current!, currentQuestion.id, answer)

    if (result.correct) {
      const newScore = result.totalPoints
      setScore(newScore)
      scoreRef.current = newScore
      setAnswerState('correct')
      if (timeLeft <= BONUS_THRESHOLD_SECONDS) {
        setTimeLeft(prev => prev + BONUS_SECONDS)
      }
      setTimeout(() => advance(), 400)
    } else {
      setWrongOption(answer)
      setAnswerState('wrong')
      setTimeout(() => advance(), 600)
    }
  }

  useEffect(() => () => stopTimer(), [stopTimer])

  return {
    quizState,
    currentQuestion,
    score,
    timeLeft,
    answerState,
    wrongOption,
    startQuiz,
    submitAnswer,
    answeredCount: currentIndex,
  }
}
