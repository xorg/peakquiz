import { useTranslation } from '../hooks/useTranslation'
import styles from './Navigation.module.css'
import type { User } from '../types'

interface Props {
  user: User | null
  onLoginClick: () => void
  onLogoutClick: () => void
  onProfileClick: () => void
  onHomeClick: () => void
  onLeaderboardClick: () => void
}

export function Navigation({ user, onLoginClick, onLogoutClick, onProfileClick, onHomeClick, onLeaderboardClick }: Props) {
  const { t } = useTranslation()

  return (
    <nav className={styles.nav}>
      <button className={styles.brand} onClick={onHomeClick}>GIPFELRATEN</button>
      <div className={styles.actions}>
        <button className={styles.navLink} onClick={onLeaderboardClick}>
          {t('globalRankings')}
        </button>
        {user ? (
          <>
            <button className={styles.usernameBtn} onClick={onProfileClick}>
              {user.username}
            </button>
            <button className={styles.btnSecondary} onClick={onLogoutClick}>
              {t('signOut')}
            </button>
          </>
        ) : (
          <button className={styles.btnPrimary} onClick={onLoginClick}>
            {t('signIn')}
          </button>
        )}
      </div>
    </nav>
  )
}
