import { useState, useEffect } from 'react'
import { useQuiz } from '../hooks/useQuiz'
import { useAuth } from '../hooks/useAuth'
import { Timer } from '../components/Timer'
import { AnswerOption } from '../components/AnswerOption'
import { LeaderboardPage } from './LeaderboardPage'
import styles from './QuizPage.module.css'

const LABELS = ['A', 'B', 'C', 'D']
const QUIZ_DURATION = 60

export function QuizPage() {
  const {
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
    answeredCount,
  } = useQuiz()

  const { user } = useAuth()
  const [nickname, setNickname] = useState(() => localStorage.getItem('pq_nickname') ?? '')

  useEffect(() => {
    if (user && !nickname) {
      setNickname(user.username)
    }
  }, [user])

  if (quizState === 'finished') {
    return <LeaderboardPage finalScore={score} onPlayAgain={startQuiz} />
  }

  if (quizState === 'nickname') {
    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault()
      const name = nickname.trim()
      if (name) localStorage.setItem('pq_nickname', name)
      submitNickname(name)
    }

    return (
      <main className={styles.nickname}>
        <div className={styles.nicknameResult}>
          <span className={styles.nicknameScore}>{score.toLocaleString()}</span>
          <span className={styles.nicknameScoreLabel}>pts</span>
        </div>
        <form className={styles.nicknameForm} onSubmit={handleSubmit}>
          <h2 className={styles.nicknameTitle}>Enter your name for the rankings</h2>
          <input
            className={styles.nicknameInput}
            value={nickname}
            onChange={e => setNickname(e.target.value)}
            placeholder="Your name"
            maxLength={30}
            autoFocus
          />
          <div className={styles.nicknameActions}>
            <button type="submit" className={styles.nicknameSave}>Save Score</button>
            <button type="button" className={styles.nicknameSkip} onClick={() => submitNickname('')}>
              Skip
            </button>
          </div>
        </form>
      </main>
    )
  }

  if (quizState === 'idle') {
    return (
      <main className={styles.idle}>
        <h2 className={styles.idleTitle}>Ready to climb?</h2>
        <p className={styles.idleDesc}>You'll have 60 seconds to identify as many mountain peaks as possible.</p>
        <button className={styles.startBtn} onClick={startQuiz}>
          Begin Ascent
        </button>
      </main>
    )
  }

  if (!currentQuestion) return null

  return (
    <main className={styles.page}>
      <div className={styles.hud}>
        <div className={styles.timerWrapper}>
          <Timer timeLeft={timeLeft} totalTime={QUIZ_DURATION} />
        </div>
        <div className={styles.score}>
          {answerState === 'correct' && (
            <span key={answeredCount} className={styles.scoreDelta}>+{lastPoints}</span>
          )}
          <span className={styles.scoreValue}>{score.toLocaleString()}</span>
          <span className={styles.scoreLabel}>pts</span>
        </div>
        <span className={styles.progress}>{answeredCount + 1}</span>
      </div>

      <div className={`${styles.card} ${answerState === 'correct' ? styles.cardCorrect : answerState === 'wrong' ? styles.cardWrong : ''}`}>
        <div className={styles.imageWrapper}>
          <img
            key={currentQuestion.id}
            className={styles.peakImage}
            src={currentQuestion.peak.imageUrl}
            alt="Mountain peak — can you name it?"
          />
          <div className={styles.imageOverlay}>
            <p className={styles.question}>WHICH PEAK IS THIS?</p>
          </div>
        </div>

        <div className={styles.options}>
          {currentQuestion.options.map((option, i) => (
            <AnswerOption
              key={option}
              label={LABELS[i]}
              text={option}
              isCorrect={correctOption === option}
              isWrong={wrongOption === option}
              disabled={answerState !== 'unanswered'}
              onClick={() => submitAnswer(option)}
            />
          ))}
        </div>
      </div>
    </main>
  )
}
