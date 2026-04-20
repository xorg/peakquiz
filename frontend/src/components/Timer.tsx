import { useLayoutEffect, useRef, useState } from 'react'
import styles from './Timer.module.css'

// Jagged mountain silhouette. Left base → ascending ridgeline → sharp peak at (200,2) → descending → right base.
// Halfway along the path (elapsed=0.5) lands at the summit.
const MOUNTAIN_PATH =
  'M 0,56 L 18,55 L 32,51 L 46,53 L 62,45 L 74,48 L 88,37 L 100,41 ' +
  'L 114,27 L 126,31 L 140,19 L 152,23 L 164,12 L 175,15 L 187,6 L 200,2 ' +
  'L 213,6 L 224,14 L 236,10 L 248,20 L 260,16 L 273,29 L 286,25 ' +
  'L 300,39 L 312,36 L 326,46 L 340,43 L 356,52 L 372,50 L 388,55 L 400,56'

interface Props {
  timeLeft: number
  totalTime: number
}

export function Timer({ timeLeft, totalTime }: Props) {
  const progress = timeLeft / totalTime
  const isUrgent = timeLeft <= 10

  const fillRef = useRef<SVGPathElement>(null)
  const [pathLength, setPathLength] = useState(0)
  const [dotPos, setDotPos] = useState({ x: 0, y: 56 })
  // Gate CSS transitions so they don't fire during initial measurement
  const [ready, setReady] = useState(false)

  const mm = String(Math.floor(timeLeft / 60)).padStart(2, '0')
  const ss = String(timeLeft % 60).padStart(2, '0')

  // Measure path and set initial dot position before first paint
  useLayoutEffect(() => {
    if (!fillRef.current) return
    const len = fillRef.current.getTotalLength()
    const pt = fillRef.current.getPointAtLength((1 - progress) * len)
    setPathLength(len)
    setDotPos({ x: pt.x, y: pt.y })
    // Enable transitions one frame later so the initial render is instant
    requestAnimationFrame(() => setReady(true))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Update dot position on each timer tick
  useLayoutEffect(() => {
    if (!fillRef.current || pathLength === 0) return
    const pt = fillRef.current.getPointAtLength((1 - progress) * pathLength)
    setDotPos({ x: pt.x, y: pt.y })
  }, [progress, pathLength])

  const dashOffset = pathLength > 0 ? pathLength * progress : 9999

  return (
    <div className={`${styles.timer} ${isUrgent ? styles.urgent : ''}`}>
      <div
        className={styles.track}
        role="progressbar"
        aria-valuenow={timeLeft}
        aria-valuemin={0}
        aria-valuemax={totalTime}
      >
        <svg
          className={styles.mountain}
          viewBox="0 0 400 62"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <path d={MOUNTAIN_PATH} className={styles.mountainBg} />
          <path
            ref={fillRef}
            d={MOUNTAIN_PATH}
            className={styles.mountainFill}
            style={{
              strokeDasharray: pathLength || 9999,
              strokeDashoffset: dashOffset,
              transition: ready ? 'stroke-dashoffset 1s linear' : 'none',
            }}
          />
          {/* cx/cy use SVG user coordinates, which scale correctly with the viewBox */}
          <circle
            cx={dotPos.x}
            cy={dotPos.y}
            r={4}
            className={`${styles.indicator} ${ready ? styles.indicatorReady : ''}`}
          />
        </svg>
      </div>
      <span className={styles.label}>{mm}:{ss}</span>
    </div>
  )
}
