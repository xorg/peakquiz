import { useTranslation } from '../hooks/useTranslation'
import styles from './Navigation.module.css'
import type { User } from '../types'

interface Props {
  user: User | null
  onLoginClick: () => void
  onLogoutClick: () => void
  onProfileClick: () => void
  onHomeClick: () => void
}

export function Navigation({ user, onLoginClick, onLogoutClick, onProfileClick, onHomeClick }: Props) {
  const { t } = useTranslation()

  return (
    <nav className={styles.nav}>
      <button className={styles.brand} onClick={onHomeClick}>PEAKQUIZ</button>
      <div className={styles.actions}>
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
