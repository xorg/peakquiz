import { useState, useEffect } from 'react'
import { Pencil } from 'lucide-react'
import { api } from '../services/api'
import { useAuth } from '../hooks/useAuth'
import { useTranslation } from '../hooks/useTranslation'
import type { ProfileStats, GameEntry } from '../types'
import styles from './ProfilePage.module.css'

function getGuestId(): string | undefined {
  return localStorage.getItem('pq_guest_id') ?? undefined
}

export function ProfilePage() {
  const [stats, setStats] = useState<ProfileStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [nicknameInput, setNicknameInput] = useState('')
  const [saving, setSaving] = useState(false)
  const { refresh } = useAuth()
  const { t } = useTranslation()

  useEffect(() => {
    api.profile.stats(getGuestId())
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false))
  }, [])

  const handleSave = async () => {
    const name = nicknameInput.trim()
    if (!name || !stats) return
    setSaving(true)
    try {
      const guestId = stats.isGuest ? stats.userId : undefined
      await api.profile.updateNickname(name, guestId)
      setStats({ ...stats, username: name })
      setEditing(false)
      if (stats.isGuest) localStorage.setItem('pq_nickname', name)
      else refresh()
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <main className={styles.page}><p className={styles.loading}>{t('loadingRankings')}</p></main>
  if (!stats) return <main className={styles.page}><p className={styles.empty}>{t('profileEmptyGuest')}</p></main>

  return (
    <main className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>{t('profileTitle')}</h1>
        {editing ? (
          <div className={styles.nicknameEdit}>
            <input
              className={styles.nicknameInput}
              value={nicknameInput}
              onChange={e => setNicknameInput(e.target.value)}
              maxLength={30}
              autoFocus
            />
            <button className={styles.nicknameSave} onClick={handleSave} disabled={saving}>
              {t('nicknameSave')}
            </button>
            <button className={styles.nicknameSkip} onClick={() => setEditing(false)}>
              {t('nicknameSkip')}
            </button>
          </div>
        ) : (
          <button
            className={styles.nicknameDisplay}
            onClick={() => { setNicknameInput(stats.username); setEditing(true) }}
          >
            <span>{stats.username}</span>
            <Pencil size={14} strokeWidth={1.75} />
          </button>
        )}
      </div>

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
