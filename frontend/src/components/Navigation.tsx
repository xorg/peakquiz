import styles from './Navigation.module.css'
import type { User } from '../types'

interface Props {
  user: User | null
  onLoginClick: () => void
  onLogoutClick: () => void
}

export function Navigation({ user, onLoginClick, onLogoutClick }: Props) {
  return (
    <nav className={styles.nav}>
      <span className={styles.brand}>PEAKQUIZ</span>
      <div className={styles.actions}>
        {user ? (
          <>
            <span className={styles.username}>{user.username}</span>
            <button className={styles.btnSecondary} onClick={onLogoutClick}>
              Sign out
            </button>
          </>
        ) : (
          <button className={styles.btnPrimary} onClick={onLoginClick}>
            Sign in with Google
          </button>
        )}
      </div>
    </nav>
  )
}
