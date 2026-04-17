import { Trophy, Award } from 'lucide-react'
import styles from './LeaderboardTable.module.css'
import type { RankingEntry } from '../types'

interface Props {
  entries: RankingEntry[]
}

function RankIcon({ rank }: { rank: number }) {
  if (rank === 1) return <Trophy size={18} strokeWidth={1.5} className={styles.rankFirst} />
  if (rank === 2) return <Award size={18} strokeWidth={1.5} className={styles.rankSecond} />
  if (rank === 3) return <Award size={18} strokeWidth={1.5} className={styles.rankThird} />
  return <span>{`#${rank}`}</span>
}

export function LeaderboardTable({ entries }: Props) {
  return (
    <div className={styles.table}>
      {entries.map((entry) => (
        <div
          key={entry.rank}
          className={`${styles.row} ${entry.isCurrentUser ? styles.highlighted : ''}`}
        >
          <span className={styles.rank}>
            <RankIcon rank={entry.rank} />
          </span>
          <span className={styles.username}>{entry.username}</span>
          <span className={styles.score}>{entry.score.toLocaleString()}</span>
        </div>
      ))}
    </div>
  )
}
