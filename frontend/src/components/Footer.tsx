import { useTranslation } from '../hooks/useTranslation'
import styles from './Footer.module.css'

export function Footer() {
  const { t } = useTranslation()
  const year = new Date().getFullYear()
  return (
    <footer className={styles.footer}>
      <span>© {year} Gipfelraten</span>
      <span className={styles.sep}>·</span>
      <a href="mailto:info@gipfelraten.ch">{t('footerContact')}</a>
    </footer>
  )
}
