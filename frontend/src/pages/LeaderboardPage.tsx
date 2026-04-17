import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { useTranslation } from '../hooks/useTranslation'
import { LeaderboardTable } from '../components/LeaderboardTable'
import type { RankingEntry } from '../types'
import styles from './LeaderboardPage.module.css'

interface Props {
  finalScore?: number
  onPlayAgain?: () => void
}

export function LeaderboardPage({ finalScore, onPlayAgain }: Props) {
  const [entries, setEntries] = useState<RankingEntry[]>([])
  const [loading, setLoading] = useState(true)
  const { t } = useTranslation()

  useEffect(() => {
    api.rankings.global()
      .then(setEntries)
      .catch(() => setEntries([]))
      .finally(() => setLoading(false))
  }, [])

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

      <section className={styles.leaderboard}>
        <h2 className={styles.sectionTitle}>{t('globalRankings')}</h2>
        {loading ? (
          <p className={styles.loading}>{t('loadingRankings')}</p>
        ) : (
          <LeaderboardTable entries={entries} />
        )}
      </section>
    </main>
  )
}
