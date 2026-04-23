import { useState, useEffect } from 'react'
import { Check, X, ChevronDown } from 'lucide-react'
import { api } from '../services/api'
import { useTranslation } from '../hooks/useTranslation'
import { LeaderboardTable } from '../components/LeaderboardTable'
import type { RankingEntry, AnswerRecord } from '../types'
import styles from './LeaderboardPage.module.css'

const CATEGORY_ALL = 'all'

interface Props {
  finalScore?: number
  onPlayAgain?: () => void
  onPlay?: () => void
  answerHistory?: AnswerRecord[]
  activeCategory?: string
}

export function LeaderboardPage({ finalScore, onPlayAgain, onPlay, answerHistory, activeCategory }: Props) {
  const [breakdownOpen, setBreakdownOpen] = useState(false)
  const [entries, setEntries] = useState<RankingEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTab, setSelectedTab] = useState<string>(activeCategory ?? CATEGORY_ALL)
  const [tabs, setTabs] = useState<{ id: string; label: string }[]>([])
  const { t } = useTranslation()

  // Fetch category list once to build tabs
  useEffect(() => {
    api.quiz.categories()
      .then(cats => {
        setTabs(cats.map(c => ({ id: c.id, label: c.name })))
      })
      .catch(() => {
        setTabs([{ id: CATEGORY_ALL, label: t('categoryAllPeaks') }])
      })
  }, [])

  useEffect(() => {
    setLoading(true)
    const fetch = api.rankings.byCategory(selectedTab)
    fetch
      .then(setEntries)
      .catch(() => setEntries([]))
      .finally(() => setLoading(false))
  }, [selectedTab])

  return (
    <main className={styles.page}>
      {finalScore !== undefined && (
        <div className={styles.result}>
          <p className={styles.resultLabel}>{t('yourScore')}</p>
          <p className={styles.resultScore}>{finalScore.toLocaleString()}</p>
          {onPlayAgain && (
            <button className={styles.playAgain} onClick={onPlayAgain}>
              {t('playAgain')}
            </button>
          )}
        </div>
      )}

      {answerHistory && answerHistory.length > 0 && (
        <section className={styles.breakdown}>
          <button
            className={styles.breakdownToggle}
            onClick={() => setBreakdownOpen(v => !v)}
            aria-expanded={breakdownOpen}
          >
            <span>{t('breakdownTitle')}</span>
            <ChevronDown
              size={18}
              className={`${styles.chevron} ${breakdownOpen ? styles.chevronOpen : ''}`}
            />
          </button>
          {breakdownOpen && (
            <div className={styles.breakdownList}>
              {answerHistory.map((a, i) => (
                <div key={i} className={styles.breakdownItem}>
                  <img src={a.peak.imageUrl} alt={a.peak.name} className={styles.breakdownImage} />
                  <span className={styles.breakdownName}>{a.peak.name}</span>
                  {a.wasCorrect ? (
                    <Check size={18} className={styles.iconCorrect} />
                  ) : (
                    <X size={18} className={styles.iconWrong} />
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {onPlay && finalScore === undefined && (
        <div className={styles.playRow}>
          <button className={styles.playAgain} onClick={onPlay}>{t('quizStart')}</button>
        </div>
      )}

      <section className={styles.leaderboard}>
        <h2 className={styles.sectionTitle}>{t('globalRankings')}</h2>

        {tabs.length > 1 && (
          <div className={styles.tabs}>
            {tabs.map(tab => (
              <button
                key={tab.id}
                className={`${styles.tab} ${selectedTab === tab.id ? styles.tabActive : ''}`}
                onClick={() => setSelectedTab(tab.id)}
              >
                {tab.id === CATEGORY_ALL ? t('rankingsTabAll') : tab.label}
              </button>
            ))}
          </div>
        )}

        {loading ? (
          <p className={styles.loading}>{t('loadingRankings')}</p>
        ) : (
          <LeaderboardTable entries={entries} />
        )}
      </section>
    </main>
  )
}
