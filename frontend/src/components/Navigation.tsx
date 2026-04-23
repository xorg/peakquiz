import { Trophy, User as UserIcon, LogIn, LogOut, Shield } from 'lucide-react'
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
  onAdminClick: () => void
}

export function Navigation({ user, onLoginClick, onLogoutClick, onProfileClick, onHomeClick, onLeaderboardClick, onAdminClick }: Props) {
  const { t } = useTranslation()

  return (
    <nav className={styles.nav}>
      <button className={styles.brand} onClick={onHomeClick}>GIPFELRATEN</button>
      <div className={styles.actions}>
        <button className={styles.navLink} onClick={onLeaderboardClick}>
          <Trophy size={18} />
          <span className={styles.label}>{t('globalRankings')}</span>
        </button>
        {user?.is_admin && (
          <button className={styles.navLink} onClick={onAdminClick}>
            <Shield size={18} />
            <span className={styles.label}>Admin</span>
          </button>
        )}
        <button className={styles.navLink} onClick={onProfileClick}>
          <UserIcon size={18} />
          <span className={styles.label}>{user ? user.username : t('profileTitle')}</span>
        </button>
        {user ? (
          <button className={styles.btnSecondary} onClick={onLogoutClick}>
            <LogOut size={18} />
            <span className={styles.label}>{t('signOut')}</span>
          </button>
        ) : (
          <button className={styles.btnPrimary} onClick={onLoginClick}>
            <LogIn size={18} />
            <span className={styles.label}>{t('signIn')}</span>
          </button>
        )}
      </div>
    </nav>
  )
}
