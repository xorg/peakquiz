import { Timer, MountainSnow, Trophy } from 'lucide-react'
import styles from './LandingPage.module.css'

interface Props {
  onStart: () => void
}

export function LandingPage({ onStart }: Props) {
  return (
    <main className={styles.page}>
      <div className={styles.hero}>
        <img
          className={styles.heroImage}
          src="/splash.jpg"
          alt="View from a rocky Alpine ledge into a mist-filled valley"
        />
        <div className={styles.colorLayer} />
        <div className={styles.overlay} />
        <div className={styles.heroContent}>
          <p className={styles.eyebrow}>THE MOUNTAIN CHALLENGE</p>
          <h1 className={styles.headline}>
            How well do you know the world's peaks?
          </h1>
          <p className={styles.tagline}>
            60 seconds. Mountain photos. How many can you name?
          </p>
          <button className={styles.ctaButton} onClick={onStart}>
            Start the Quiz
          </button>
        </div>
      </div>

      <section className={styles.features}>
        <div className={styles.feature}>
          <Timer className={styles.featureIcon} strokeWidth={1.5} />
          <h3>Timed Challenge</h3>
          <p>60 seconds to name as many peaks as you can</p>
        </div>
        <div className={styles.feature}>
          <MountainSnow className={styles.featureIcon} strokeWidth={1.5} />
          <h3>Real Photos</h3>
          <p>Identify peaks from stunning mountain photography</p>
        </div>
        <div className={styles.feature}>
          <Trophy className={styles.featureIcon} strokeWidth={1.5} />
          <h3>Global Ranking</h3>
          <p>See how you compare to mountain enthusiasts worldwide</p>
        </div>
      </section>
    </main>
  )
}
