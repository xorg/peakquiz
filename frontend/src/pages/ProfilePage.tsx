import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { useTranslation } from '../hooks/useTranslation'
import type { ProfileStats, GameEntry } from '../types'
import styles from './ProfilePage.module.css'

export function ProfilePage() {
  const [stats, setStats] = useState<ProfileStats | null>(null)
  const [loading, setLoading] = useState(true)
  const { t } = useTranslation()

  useEffect(() => {
    api.profile.stats()
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <main className={styles.page}><p className={styles.loading}>{t('loadingRankings')}</p></main>
  if (!stats) return null

  return (
    <main className={styles.page}>
      <h1 className={styles.title}>{t('profileTitle')}</h1>

      <div className={styles.statsRow}>
        <div className={styles.statCard}>
          <span className={styles.statValue}>{stats.totalGuesses.toLocaleString()}</span>
          <span className={styles.statLabel}>{t('statTotalGuesses')}</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statValue}>{stats.correctGuesses.toLocaleString()}</span>
          <span className={styles.statLabel}>{t('statCorrect')}</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statValue}>{stats.accuracyPercent}%</span>
          <span className={styles.statLabel}>{t('statAccuracy')}</span>
        </div>
      </div>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>{t('recentGamesTitle')}</h2>
        {stats.recentGames.length === 0 ? (
          <p className={styles.empty}>{t('recentGamesEmpty')}</p>
        ) : (
          <div className={styles.gamesList}>
            {stats.recentGames.map((game: GameEntry) => (
              <div key={game.id} className={styles.gameRow}>
                <span className={styles.gameScore}>{game.score} {t('pts')}</span>
                <span className={styles.gameCounts}>
                  <span className={styles.gameCorrect}>{game.correctCount} {t('gameCorrect')}</span>
                  <span className={styles.gameSep}>·</span>
                  <span className={styles.gameWrong}>{game.wrongCount} {t('gameWrong')}</span>
                </span>
                <span className={styles.gameDate}>
                  {new Date(game.playedAt).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>{t('troublePeaksTitle')}</h2>
        {stats.troublePeaks.length === 0 ? (
          <p className={styles.empty}>{t('troublePeaksEmpty')}</p>
        ) : (
          <div className={styles.peaksGrid}>
            {stats.troublePeaks.map(peak => (
              <div key={peak.peakId} className={styles.peakCard}>
                <div className={styles.peakImageWrapper}>
                  <img
                    className={styles.peakImage}
                    src={peak.imageUrl}
                    alt={peak.peakName}
                  />
                </div>
                <div className={styles.peakInfo}>
                  <span className={styles.peakName}>{peak.peakName}</span>
                  <span className={styles.peakStat}>
                    {peak.wrongCount} {t('wrong')} · {peak.totalAttempts} {t('attempts')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}
