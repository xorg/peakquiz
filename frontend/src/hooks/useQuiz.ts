import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '../services/api'
import type { QuizSession, QuizQuestion, AnswerState, QuizState } from '../types'

const QUIZ_DURATION_SECONDS = 60

export function useQuiz() {
  const [quizState, setQuizState] = useState<QuizState>('idle')
  const [session, setSession] = useState<QuizSession | null>(null)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [score, setScore] = useState(0)
  const [timeLeft, setTimeLeft] = useState(QUIZ_DURATION_SECONDS)
  const [answerState, setAnswerState] = useState<AnswerState>('unanswered')
  const [wrongAnswers, setWrongAnswers] = useState<Set<string>>(new Set())
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const currentQuestion: QuizQuestion | null = session?.questions[currentIndex] ?? null

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const finishQuiz = useCallback(async (finalScore: number, sessionId: string) => {
    stopTimer()
    setQuizState('finished')
    try {
      await api.quiz.finish(sessionId, finalScore)
    } catch {
      // score still shown locally even if save fails
    }
  }, [stopTimer])

  const startQuiz = async () => {
    setScore(0)
    setCurrentIndex(0)
    setAnswerState('unanswered')
    setWrongAnswers(new Set())
    setTimeLeft(QUIZ_DURATION_SECONDS)

    const newSession = await api.quiz.start()
    setSession(newSession)
    setQuizState('active')

    timerRef.current = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          finishQuiz(score, newSession.sessionId)
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }

  const submitAnswer = async (answer: string) => {
    if (!session || !currentQuestion || answerState !== 'unanswered') return

    const result = await api.quiz.answer(session.sessionId, currentQuestion.id, answer)

    if (result.correct) {
      setScore(result.totalPoints)
      setAnswerState('correct')
      setTimeout(() => {
        setAnswerState('unanswered')
        setWrongAnswers(new Set())
        if (currentIndex + 1 >= session.questions.length) {
          finishQuiz(result.totalPoints, session.sessionId)
        } else {
          setCurrentIndex(i => i + 1)
        }
      }, 800)
    } else {
      setWrongAnswers(prev => new Set(prev).add(answer))
      setAnswerState('wrong')
      setTimeout(() => setAnswerState('unanswered'), 600)
    }
  }

  useEffect(() => () => stopTimer(), [stopTimer])

  return {
    quizState,
    currentQuestion,
    score,
    timeLeft,
    answerState,
    wrongAnswers,
    startQuiz,
    submitAnswer,
    totalQuestions: session?.questions.length ?? 0,
    currentIndex,
  }
}
