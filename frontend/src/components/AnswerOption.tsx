import { Check, X } from 'lucide-react'
import styles from './AnswerOption.module.css'

interface Props {
  label: string
  text: string
  isCorrect: boolean
  isWrong: boolean
  disabled: boolean
  onClick: () => void
}

export function AnswerOption({ label, text, isCorrect, isWrong, disabled, onClick }: Props) {
  return (
    <button
      className={`${styles.option} ${isCorrect ? styles.correct : ''} ${isWrong ? styles.wrong : ''}`}
      disabled={disabled && !isWrong && !isCorrect}
      onClick={onClick}
    >
      <span className={styles.label}>
        {isCorrect
          ? <Check size={16} strokeWidth={2.5} />
          : isWrong
            ? <X size={16} strokeWidth={2.5} />
            : label}
      </span>
      <span className={styles.text}>{text}</span>
    </button>
  )
}
