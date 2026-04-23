import { useState, useEffect, useCallback } from 'react'
import { Search, Trash2, Plus, ExternalLink } from 'lucide-react'
import { api } from '../services/api'
import styles from './AdminPage.module.css'
import type { AdminPeak, AdminPeakDetail, WikiSearchResult } from '../types'

type FilterPics = 'all' | 'yes' | 'no'

export function AdminPage() {
  // List state
  const [peaks, setPeaks] = useState<AdminPeak[]>([])
  const [search, setSearch] = useState('')
  const [filterPics, setFilterPics] = useState<FilterPics>('all')
  const [loadingList, setLoadingList] = useState(false)

  // Detail state
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [detail, setDetail] = useState<AdminPeakDetail | null>(null)
  const [editName, setEditName] = useState('')
  const [editRegion, setEditRegion] = useState('')
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [saving, setSaving] = useState(false)

  // New peak form state
  const [creatingNew, setCreatingNew] = useState(false)
  const [newName, setNewName] = useState('')
  const [newRegion, setNewRegion] = useState('')
  const [newElevation, setNewElevation] = useState('')
  const [newMountainRange, setNewMountainRange] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')

  // Wiki search state
  const [wikiQuery, setWikiQuery] = useState('')
  const [wikiResults, setWikiResults] = useState<WikiSearchResult[]>([])
  const [searchingWiki, setSearchingWiki] = useState(false)
  const [addingPic, setAddingPic] = useState<string | null>(null)

  const loadPeaks = useCallback(async (q: string, filter: FilterPics) => {
    setLoadingList(true)
    try {
      const hasPics = filter === 'all' ? undefined : filter === 'yes'
      const data = await api.admin.peaks(q || undefined, hasPics)
      setPeaks(data)
    } finally {
      setLoadingList(false)
    }
  }, [])

  useEffect(() => {
    const t = setTimeout(() => loadPeaks(search, filterPics), search ? 300 : 0)
    return () => clearTimeout(t)
  }, [search, filterPics, loadPeaks])

  const loadDetail = useCallback(async (id: number) => {
    setLoadingDetail(true)
    setWikiResults([])
    setWikiQuery('')
    try {
      const data = await api.admin.peak(id)
      setDetail(data)
      setEditName(data.name)
      setEditRegion(data.region ?? '')
    } finally {
      setLoadingDetail(false)
    }
  }, [])

  useEffect(() => {
    if (selectedId != null) loadDetail(selectedId)
  }, [selectedId, loadDetail])

  const selectPeak = (id: number) => {
    setCreatingNew(false)
    setSelectedId(id)
  }

  const openNewPeakForm = () => {
    setSelectedId(null)
    setDetail(null)
    setNewName('')
    setNewRegion('')
    setNewElevation('')
    setNewMountainRange('')
    setCreateError('')
    setCreatingNew(true)
  }

  const createPeak = async () => {
    const name = newName.trim()
    if (!name) { setCreateError('Name is required.'); return }
    setCreating(true)
    setCreateError('')
    try {
      const created = await api.admin.createPeak({
        name,
        region: newRegion.trim() || undefined,
        elevation: newElevation ? parseInt(newElevation, 10) : undefined,
        mountain_range: newMountainRange.trim() || undefined,
      })
      setPeaks(ps => [{ id: created.id, name: created.name, region: created.region, elevation: created.elevation, picture_count: 0 }, ...ps])
      setCreatingNew(false)
      setSelectedId(created.id)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to create peak.'
      setCreateError(msg.includes('409') ? 'A peak with that name already exists.' : msg)
    } finally {
      setCreating(false)
    }
  }

  const savePeak = async () => {
    if (!detail) return
    setSaving(true)
    try {
      const updates: { name?: string; region?: string } = {}
      if (editName !== detail.name) updates.name = editName
      if (editRegion !== (detail.region ?? '')) updates.region = editRegion
      if (!Object.keys(updates).length) return
      const updated = await api.admin.updatePeak(detail.id, updates)
      setDetail(updated)
      setPeaks(ps => ps.map(p => p.id === updated.id ? { ...p, name: updated.name, region: updated.region } : p))
    } finally {
      setSaving(false)
    }
  }

  const deletePeak = async () => {
    if (!detail || !confirm(`Delete "${detail.name}" and all its pictures?`)) return
    await api.admin.deletePeak(detail.id)
    setPeaks(ps => ps.filter(p => p.id !== detail.id))
    setDetail(null)
    setSelectedId(null)
  }

  const deletePicture = async (picId: number) => {
    if (!detail || !confirm('Delete this picture?')) return
    await api.admin.deletePicture(picId)
    const newPics = detail.pictures.filter(p => p.id !== picId)
    setDetail({ ...detail, pictures: newPics })
    setPeaks(ps => ps.map(p => p.id === detail.id ? { ...p, picture_count: newPics.length } : p))
  }

  const searchWiki = async () => {
    if (!detail) return
    setSearchingWiki(true)
    try {
      const results = await api.admin.searchImages(detail.id, wikiQuery || undefined)
      setWikiResults(results)
    } finally {
      setSearchingWiki(false)
    }
  }

  const addPicture = async (r: WikiSearchResult) => {
    if (!detail) return
    setAddingPic(r.filename)
    try {
      const pic = await api.admin.addPicture(detail.id, {
        image_url: r.direct_url,
        original_url: r.direct_url,
        source: r.source,
        title: r.title,
        author_name: r.author_name,
        author_url: r.author_url,
        license_name: r.license_name,
        license_url: r.license_url,
      })
      const newPics = [...detail.pictures, pic]
      setDetail({ ...detail, pictures: newPics })
      setPeaks(ps => ps.map(p => p.id === detail.id ? { ...p, picture_count: newPics.length } : p))
      setWikiResults(rs => rs.filter(x => x.filename !== r.filename))
    } finally {
      setAddingPic(null)
    }
  }

  const isDirty = detail && (editName !== detail.name || editRegion !== (detail.region ?? ''))

  return (
    <div className={styles.layout}>
      {/* ── Left panel ── */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <div className={styles.titleRow}>
            <h1 className={styles.title}>Admin</h1>
            <button className={styles.newPeakBtn} onClick={openNewPeakForm} title="New peak">
              <Plus size={16} />
              New
            </button>
          </div>
          <div className={styles.searchRow}>
            <Search size={14} className={styles.searchIcon} />
            <input
              className={styles.searchInput}
              placeholder="Search peaks…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <div className={styles.filterRow}>
            {(['all', 'yes', 'no'] as FilterPics[]).map(f => (
              <button
                key={f}
                className={`${styles.filterBtn} ${filterPics === f ? styles.filterBtnActive : ''}`}
                onClick={() => setFilterPics(f)}
              >
                {f === 'all' ? 'All' : f === 'yes' ? 'Has pics' : 'No pics'}
              </button>
            ))}
          </div>
        </div>
        <div className={styles.peakList}>
          {loadingList ? (
            <div className={styles.listLoading}>Loading…</div>
          ) : peaks.length === 0 ? (
            <div className={styles.listLoading}>No peaks found</div>
          ) : peaks.map(peak => (
            <button
              key={peak.id}
              className={`${styles.peakItem} ${selectedId === peak.id ? styles.peakItemActive : ''}`}
              onClick={() => selectPeak(peak.id)}
            >
              <div className={styles.peakItemName}>{peak.name}</div>
              <div className={styles.peakItemMeta}>
                {peak.elevation ? `${peak.elevation} m` : '—'}
                {peak.region ? ` · ${peak.region}` : ''}
                {' · '}
                <span className={peak.picture_count === 0 ? styles.noPics : ''}>
                  {peak.picture_count} pic{peak.picture_count !== 1 ? 's' : ''}
                </span>
              </div>
            </button>
          ))}
        </div>
      </aside>

      {/* ── Right panel ── */}
      <main className={styles.detail}>
        {creatingNew ? (
          <div className={styles.newPeakForm}>
            <h2 className={styles.sectionTitle}>New Peak</h2>
            <div className={styles.formGrid}>
              <label className={styles.formLabel}>
                Name *
                <input
                  className={styles.formInput}
                  placeholder="e.g. Matterhorn"
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && createPeak()}
                  autoFocus
                />
              </label>
              <label className={styles.formLabel}>
                Region
                <input
                  className={styles.formInput}
                  placeholder="e.g. Valais"
                  value={newRegion}
                  onChange={e => setNewRegion(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && createPeak()}
                />
              </label>
              <label className={styles.formLabel}>
                Elevation (m)
                <input
                  className={styles.formInput}
                  type="number"
                  placeholder="e.g. 4478"
                  value={newElevation}
                  onChange={e => setNewElevation(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && createPeak()}
                />
              </label>
              <label className={styles.formLabel}>
                Mountain range
                <input
                  className={styles.formInput}
                  placeholder="e.g. Pennine Alps"
                  value={newMountainRange}
                  onChange={e => setNewMountainRange(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && createPeak()}
                />
              </label>
            </div>
            {createError && <p className={styles.formError}>{createError}</p>}
            <div className={styles.formActions}>
              <button className={styles.saveBtn} onClick={createPeak} disabled={creating}>
                {creating ? 'Creating…' : 'Create Peak'}
              </button>
              <button className={styles.cancelBtn} onClick={() => setCreatingNew(false)}>
                Cancel
              </button>
            </div>
          </div>
        ) : selectedId == null ? (
          <div className={styles.emptyDetail}>Select a peak to edit</div>
        ) : loadingDetail ? (
          <div className={styles.emptyDetail}>Loading…</div>
        ) : detail ? (
          <>
            {/* Header */}
            <div className={styles.detailHeader}>
              <div className={styles.editRow}>
                <input
                  className={styles.nameInput}
                  value={editName}
                  onChange={e => setEditName(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && savePeak()}
                />
                <input
                  className={styles.regionInput}
                  placeholder="Region"
                  value={editRegion}
                  onChange={e => setEditRegion(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && savePeak()}
                />
                <button
                  className={styles.saveBtn}
                  onClick={savePeak}
                  disabled={saving || !isDirty}
                >
                  {saving ? 'Saving…' : 'Save'}
                </button>
                <button className={styles.deleteBtn} onClick={deletePeak} title="Delete peak">
                  <Trash2 size={16} />
                </button>
              </div>
              {detail.elevation != null && (
                <div className={styles.meta}>
                  {detail.elevation} m
                  {detail.mountain_range ? ` · ${detail.mountain_range}` : ''}
                  {detail.peak_type ? ` · ${detail.peak_type}` : ''}
                </div>
              )}
            </div>

            {/* Pictures */}
            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>
                Pictures ({detail.pictures.length})
              </h2>
              {detail.pictures.length === 0 ? (
                <p className={styles.emptySection}>No pictures yet.</p>
              ) : (
                <div className={styles.pictureGrid}>
                  {detail.pictures.map(pic => (
                    <div key={pic.id} className={styles.pictureCard}>
                      <img
                        className={styles.pictureThumb}
                        src={pic.cdn_url ?? pic.original_url}
                        alt={pic.title ?? ''}
                        loading="lazy"
                      />
                      <div className={styles.pictureMeta}>
                        {pic.author_name && <span>{pic.author_name}</span>}
                        {pic.license_name && <span>{pic.license_name}</span>}
                      </div>
                      <div className={styles.cardActions}>
                        {pic.source && (
                          <a
                            href={pic.source}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={styles.iconBtn}
                            title="Open source"
                          >
                            <ExternalLink size={13} />
                          </a>
                        )}
                        <button
                          className={styles.iconBtnDanger}
                          onClick={() => deletePicture(pic.id)}
                          title="Delete picture"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Wikimedia search */}
            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>Add Picture from Wikimedia</h2>
              <div className={styles.wikiSearchRow}>
                <input
                  className={styles.wikiInput}
                  placeholder={`Search for "${detail.name}"…`}
                  value={wikiQuery}
                  onChange={e => setWikiQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && searchWiki()}
                />
                <button
                  className={styles.searchWikiBtn}
                  onClick={searchWiki}
                  disabled={searchingWiki}
                >
                  {searchingWiki ? 'Searching…' : 'Search'}
                </button>
              </div>
              {wikiResults.length > 0 && (
                <div className={styles.pictureGrid}>
                  {wikiResults.map(r => (
                    <div key={r.filename} className={styles.pictureCard}>
                      <img
                        className={styles.pictureThumb}
                        src={r.direct_url}
                        alt={r.title}
                        loading="lazy"
                      />
                      <div className={styles.pictureMeta}>
                        <span title={r.title.replace('File:', '')}>{r.title.replace('File:', '')}</span>
                        {r.author_name && <span>{r.author_name}{r.license_name ? ` · ${r.license_name}` : ''}</span>}
                      </div>
                      <div className={styles.cardActions}>
                        <a
                          href={r.source}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={styles.iconBtn}
                          title="Open on Wikimedia"
                        >
                          <ExternalLink size={13} />
                        </a>
                        <button
                          className={styles.addPicBtn}
                          onClick={() => addPicture(r)}
                          disabled={addingPic === r.filename}
                          title="Add this picture"
                        >
                          {addingPic === r.filename ? '…' : <Plus size={14} />}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        ) : null}
      </main>
    </div>
  )
}
