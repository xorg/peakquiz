import { useState, useEffect } from 'react'
import { useQuiz } from '../hooks/useQuiz'
import { useAuth } from '../hooks/useAuth'
import { useTranslation } from '../hooks/useTranslation'
import { Flame } from 'lucide-react'
import { Timer } from '../components/Timer'
import { AnswerOption } from '../components/AnswerOption'
import { LeaderboardPage } from './LeaderboardPage'
import type { QuizMode } from '../hooks/useQuiz'
import styles from './QuizPage.module.css'

const LABELS = ['A', 'B', 'C', 'D']
const QUIZ_DURATION = 60

// Hint types ordered for display. Extend here to add future hints.
const HINT_TYPES: { id: string; translationKey: 'hintElevation' | 'hintRegion'; costKey: 'hintCost' }[] = [
  { id: 'elevation', translationKey: 'hintElevation', costKey: 'hintCost' },
  { id: 'region',    translationKey: 'hintRegion',    costKey: 'hintCost' },
]

const HINT_COSTS: Record<string, number> = { elevation: 25, region: 25 }

interface Props {
  category?: string
  mode?: QuizMode
  onPlayAgain: () => void
}

export function QuizPage({ category, mode = 'timed', onPlayAgain }: Props) {
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
    streak,
    multiplier,
    hintsRevealed,
    revealHint,
  } = useQuiz()

  const { user, refresh } = useAuth()
  const { t } = useTranslation()
  const [nickname, setNickname] = useState(() => localStorage.getItem('pq_nickname') ?? '')

  useEffect(() => {
    startQuiz(category, mode)
  }, [])

  useEffect(() => {
    if (user && !nickname) setNickname(user.username)
  }, [user])

  if (quizState === 'finished') {
    return (
      <LeaderboardPage
        finalScore={score}
        onPlayAgain={onPlayAgain}
        answerHistory={answerHistory}
        activeCategory={category}
        activeMode={mode}
      />
    )
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

  if (quizState === 'idle' || !currentQuestion) return null

  return (
    <main className={styles.page}>
      <div className={styles.hud}>
        {mode === 'timed' ? (
          <div className={styles.timerWrapper}>
            <Timer timeLeft={timeLeft} totalTime={QUIZ_DURATION} />
          </div>
        ) : (
          <div className={styles.chillBadge}>{t('modeChill')}</div>
        )}
        <div className={styles.score}>
          {answerState === 'correct' && (
            <span key={answeredCount} className={styles.scoreDelta}>+{lastPoints}</span>
          )}
          <span className={styles.scoreValue}>{score.toLocaleString()}</span>
          <span className={styles.scoreLabel}>{t('pts')}</span>
        </div>
        {multiplier > 1 && (
          <div key={streak} className={styles.streak} aria-label={`Streak ${streak}, ${multiplier}x points`}>
            <Flame size={12 + multiplier * 6} strokeWidth={2.5} />
            <span className={styles.streakMult}>{multiplier}x</span>
          </div>
        )}
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
          {(currentQuestion.peak.authorName || currentQuestion.peak.licenseName) && (
            <div className={styles.attribution}>
              {currentQuestion.peak.authorName && (
                currentQuestion.peak.authorUrl
                  ? <a href={currentQuestion.peak.authorUrl} target="_blank" rel="noopener noreferrer">{currentQuestion.peak.authorName}</a>
                  : <span>{currentQuestion.peak.authorName}</span>
              )}
              {currentQuestion.peak.authorName && currentQuestion.peak.licenseName && <span> · </span>}
              {currentQuestion.peak.licenseName && (
                currentQuestion.peak.licenseUrl
                  ? <a href={currentQuestion.peak.licenseUrl} target="_blank" rel="noopener noreferrer">{currentQuestion.peak.licenseName}</a>
                  : <span>{currentQuestion.peak.licenseName}</span>
              )}
            </div>
          )}
        </div>

        {/* Hint bar — chill mode only */}
        {mode === 'chill' && (
          <div className={styles.hintBar}>
            {HINT_TYPES.map(hint => {
              const revealed = hintsRevealed.has(hint.id)
              const cost = HINT_COSTS[hint.id] ?? 0
              const label = t(hint.translationKey)
              const value = hint.id === 'elevation'
                ? `${currentQuestion.peak.heightM} m`
                : currentQuestion.peak.country || '—'
              return (
                <div key={hint.id} className={styles.hintChip}>
                  {revealed ? (
                    <span className={styles.hintValue}><strong>{label}:</strong> {value}</span>
                  ) : (
                    <button
                      className={styles.hintBtn}
                      onClick={() => revealHint(hint.id)}
                      disabled={answerState !== 'unanswered'}
                    >
                      {label}
                      <span className={styles.hintCost}>
                        {t('hintCost').replace('{n}', String(cost))}
                      </span>
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        )}

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
