import { Timer, MountainSnow, Trophy } from 'lucide-react'
import { useTranslation } from '../hooks/useTranslation'
import styles from './LandingPage.module.css'

interface Props {
  onStart: () => void
}

export function LandingPage({ onStart }: Props) {
  const { t } = useTranslation()

  return (
    <main className={styles.page}>
      <div className={styles.hero}>
        <img
          className={styles.heroImage}
          src="/splash.jpg"
          alt={t('heroAlt')}
        />
        <div className={styles.colorLayer} />
        <div className={styles.overlay} />
        <div className={styles.heroContent}>
          <p className={styles.eyebrow}>{t('eyebrow')}</p>
          <h1 className={styles.headline}>{t('headline')}</h1>
          <p className={styles.tagline}>{t('tagline')}</p>
          <button className={styles.ctaButton} onClick={onStart}>
            {t('ctaButton')}
          </button>
        </div>
      </div>

      <section className={styles.features}>
        <div className={styles.featuresInner}>
          <div className={styles.feature}>
            <Timer className={styles.featureIcon} strokeWidth={1.5} />
            <h3>{t('feature1Title')}</h3>
            <p>{t('feature1Desc')}</p>
          </div>
          <div className={styles.feature}>
            <MountainSnow className={styles.featureIcon} strokeWidth={1.5} />
            <h3>{t('feature2Title')}</h3>
            <p>{t('feature2Desc')}</p>
          </div>
          <div className={styles.feature}>
            <Trophy className={styles.featureIcon} strokeWidth={1.5} />
            <h3>{t('feature3Title')}</h3>
            <p>{t('feature3Desc')}</p>
          </div>
        </div>
      </section>
    </main>
  )
}
