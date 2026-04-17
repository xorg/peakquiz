import styles from './LeaderboardTable.module.css'
import type { RankingEntry } from '../types'

interface Props {
  entries: RankingEntry[]
}

const MEDALS = ['🥇', '🥈', '🥉']

export function LeaderboardTable({ entries }: Props) {
  return (
    <div className={styles.table}>
      {entries.map((entry) => (
        <div
          key={entry.rank}
          className={`${styles.row} ${entry.isCurrentUser ? styles.highlighted : ''}`}
        >
          <span className={styles.rank}>
            {entry.rank <= 3 ? MEDALS[entry.rank - 1] : `#${entry.rank}`}
          </span>
          <span className={styles.username}>{entry.username}</span>
          <span className={styles.score}>{entry.score.toLocaleString()}</span>
        </div>
      ))}
    </div>
  )
}
