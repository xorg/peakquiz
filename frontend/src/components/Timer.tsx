import styles from './Timer.module.css'

interface Props {
  timeLeft: number
  totalTime: number
}

export function Timer({ timeLeft, totalTime }: Props) {
  const progress = timeLeft / totalTime
  const isUrgent = timeLeft <= 10

  const mm = String(Math.floor(timeLeft / 60)).padStart(2, '0')
  const ss = String(timeLeft % 60).padStart(2, '0')

  return (
    <div className={`${styles.timer} ${isUrgent ? styles.urgent : ''}`}>
      <div
        className={styles.track}
        role="progressbar"
        aria-valuenow={timeLeft}
        aria-valuemin={0}
        aria-valuemax={totalTime}
      >
        <div className={styles.fill} style={{ width: `${progress * 100}%` }} />
        <div className={styles.peak} style={{ left: `${progress * 100}%` }} />
      </div>
      <span className={styles.label}>{mm}:{ss}</span>
    </div>
  )
}
