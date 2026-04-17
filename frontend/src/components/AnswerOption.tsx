import styles from './AnswerOption.module.css'

interface Props {
  label: string
  text: string
  isWrong: boolean
  disabled: boolean
  onClick: () => void
}

export function AnswerOption({ label, text, isWrong, disabled, onClick }: Props) {
  return (
    <button
      className={`${styles.option} ${isWrong ? styles.wrong : ''}`}
      disabled={disabled && !isWrong}
      onClick={onClick}
    >
      <span className={styles.label}>{label}</span>
      <span className={styles.text}>{text}</span>
    </button>
  )
}
