import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { useTranslation } from '../hooks/useTranslation'
import { cdnUrl } from '../utils/cloudinary'
import type { Category } from '../types'
import styles from './CategoryPage.module.css'

const CATEGORY_ALL = 'all'

type Mode = 'timed' | 'chill'

interface Props {
  onStart: (category: string, mode: Mode) => void
}

export function CategoryPage({ onStart }: Props) {
  const { t } = useTranslation()
  const [categories, setCategories] = useState<Category[]>([])
  const [selected, setSelected] = useState<string>(CATEGORY_ALL)
  const [mode, setMode] = useState<Mode>('timed')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.quiz.categories()
      .then(setCategories)
      .catch(() => setCategories([]))
      .finally(() => setLoading(false))
  }, [])

  const featured = categories.find(c => c.id === CATEGORY_ALL)
  const regional = categories.filter(c => c.id !== CATEGORY_ALL)

  return (
    <main className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>{t('categoryTitle')}</h1>
        <p className={styles.subtitle}>{t('categorySubtitle')}</p>
      </div>

      {loading ? (
        <div className={styles.skeleton}>
          <div className={styles.skeletonFeatured} />
          <div className={styles.skeletonGrid}>
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className={styles.skeletonCard} />
            ))}
          </div>
        </div>
      ) : (
        <div className={styles.cards}>
          {featured && (
            <button
              className={`${styles.featured} ${selected === CATEGORY_ALL ? styles.selectedFeatured : ''}`}
              onClick={() => setSelected(CATEGORY_ALL)}
            >
              <img src={cdnUrl(featured.imageUrl, 600)} alt={featured.name} className={styles.featuredImg} />
              <div className={styles.featuredOverlay} />
              <div className={styles.featuredContent}>
                <span className={styles.featuredEyebrow}>{t('categoryAllPeaks')}</span>
                <span className={styles.featuredCount}>{featured.peakCount} {t('categoryPeaks')}</span>
              </div>
              {selected === CATEGORY_ALL && <span className={styles.checkmark}>✓</span>}
            </button>
          )}

          <div className={styles.grid}>
            {regional.map(cat => (
              <button
                key={cat.id}
                className={`${styles.card} ${selected === cat.id ? styles.selectedCard : ''}`}
                onClick={() => setSelected(cat.id)}
              >
                <img src={cdnUrl(cat.imageUrl, 400)} alt={cat.name} className={styles.cardImg} />
                <div className={styles.cardOverlay} />
                <div className={styles.cardContent}>
                  <span className={styles.cardName}>{cat.name}</span>
                  <span className={styles.cardCount}>{cat.peakCount} {t('categoryPeaks')}</span>
                </div>
                {selected === cat.id && <span className={styles.checkmark}>✓</span>}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className={styles.modeToggle}>
        {([
          { id: 'timed' as Mode, label: t('modeTimed'), desc: t('modeTimedDesc') },
          { id: 'chill' as Mode, label: t('modeChill'), desc: t('modeChillDesc') },
        ]).map(m => (
          <button
            key={m.id}
            className={`${styles.modeBtn} ${mode === m.id ? styles.modeBtnActive : ''}`}
            onClick={() => setMode(m.id)}
          >
            <span className={styles.modeBtnLabel}>{m.label}</span>
            <span className={styles.modeBtnDesc}>{m.desc}</span>
          </button>
        ))}
      </div>

      <div className={styles.footer}>
        <button
          className={styles.startBtn}
          onClick={() => onStart(selected, mode)}
          disabled={loading}
        >
          {t('categoryStartBtn')}
        </button>
      </div>
    </main>
  )
}
