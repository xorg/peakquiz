import { useQuiz } from '../hooks/useQuiz'
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
    wrongAnswers,
    startQuiz,
    submitAnswer,
    totalQuestions,
    currentIndex,
  } = useQuiz()

  if (quizState === 'finished') {
    return <LeaderboardPage finalScore={score} onPlayAgain={startQuiz} />
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
          <span className={styles.scoreValue}>{score.toLocaleString()}</span>
          <span className={styles.scoreLabel}>pts</span>
        </div>
        <span className={styles.progress}>{currentIndex + 1} / {totalQuestions}</span>
      </div>

      <div className={styles.card}>
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
              isWrong={wrongAnswers.has(option)}
              disabled={answerState === 'correct'}
              onClick={() => submitAnswer(option)}
            />
          ))}
        </div>
      </div>
    </main>
  )
}
