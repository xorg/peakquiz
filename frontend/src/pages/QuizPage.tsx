import { useState, useEffect } from 'react'
import { useQuiz } from '../hooks/useQuiz'
import { useAuth } from '../hooks/useAuth'
import { useTranslation } from '../hooks/useTranslation'
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
    wrongCount,
    maxWrong,
    answerHistory,
  } = useQuiz()

  const { user, refresh } = useAuth()
  const { t } = useTranslation()
  const [nickname, setNickname] = useState(() => localStorage.getItem('pq_nickname') ?? '')

  useEffect(() => {
    if (user && !nickname) {
      setNickname(user.username)
    }
  }, [user])

  if (quizState === 'finished') {
    return <LeaderboardPage finalScore={score} onPlayAgain={startQuiz} answerHistory={answerHistory} />
  }

  if (quizState === 'nickname') {
    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault()
      const name = nickname.trim()
      if (name) localStorage.setItem('pq_nickname', name)
      await submitNickname(name)
      if (user && name) refresh()
    }

    return (
      <main className={styles.nickname}>
        <div className={styles.nicknameResult}>
          <span className={styles.nicknameScore}>{score.toLocaleString()}</span>
          <span className={styles.nicknameScoreLabel}>{t('pts')}</span>
        </div>
        <form className={styles.nicknameForm} onSubmit={handleSubmit}>
          <h2 className={styles.nicknameTitle}>{t('nicknameTitle')}</h2>
          <input
            className={styles.nicknameInput}
            value={nickname}
            onChange={e => setNickname(e.target.value)}
            placeholder={t('nicknamePlaceholder')}
            maxLength={30}
            autoFocus
          />
          <div className={styles.nicknameActions}>
            <button type="submit" className={styles.nicknameSave}>{t('nicknameSave')}</button>
            <button type="button" className={styles.nicknameSkip} onClick={() => submitNickname('')}>
              {t('nicknameSkip')}
            </button>
          </div>
        </form>
      </main>
    )
  }

  if (quizState === 'idle') {
    return (
      <main className={styles.idle}>
        <h2 className={styles.idleTitle}>{t('quizIdleTitle')}</h2>
        <p className={styles.idleDesc}>{t('quizIdleDesc')}</p>
        <button className={styles.startBtn} onClick={startQuiz}>
          {t('quizStart')}
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
          <span className={styles.scoreLabel}>{t('pts')}</span>
        </div>
        <div className={styles.lives} aria-label={`${maxWrong - wrongCount} wrong answers left`}>
          {Array.from({ length: maxWrong }).map((_, i) => (
            <span
              key={i}
              className={`${styles.life} ${i < wrongCount ? styles.lifeLost : ''}`}
            />
          ))}
        </div>
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
            <p className={styles.question}>{t('quizQuestion')}</p>
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
