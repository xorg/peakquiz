from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ...db.database import get_db
from ...db.models import Peak, Picture, User
from ...schemas.admin import (
    AddPictureRequest,
    PeakDetail,
    PeakListItem,
    PeakUpdate,
    PictureItem,
    WikiResult,
)
from ...utils.media import PictureUploader
from ...utils.wikimedia import WikimediaClient
from .auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])
_wiki = WikimediaClient()


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _picture_item(pic: Picture) -> PictureItem:
    return PictureItem(
        id=pic.id,
        cdn_url=pic.cdn_url,
        original_url=pic.original_url,
        title=pic.title,
        author_name=pic.author_rel.name if pic.author_rel else pic.author,
        author_url=pic.author_rel.url if pic.author_rel else None,
        license_name=pic.license_rel.name if pic.license_rel else None,
        license_url=pic.license_rel.url if pic.license_rel else None,
        source=pic.source,
    )


def _load_peak_detail(peak_id: int, db: Session) -> Peak:
    peak = (
        db.query(Peak)
        .options(
            joinedload(Peak.pictures).joinedload(Picture.author_rel),
            joinedload(Peak.pictures).joinedload(Picture.license_rel),
        )
        .filter(Peak.id == peak_id)
        .first()
    )
    if not peak:
        raise HTTPException(status_code=404, detail="Peak not found")
    return peak


def _peak_detail_response(peak: Peak) -> PeakDetail:
    return PeakDetail(
        id=peak.id,
        name=peak.name,
        region=peak.region,
        elevation=peak.elevation,
        mountain_range=peak.mountain_range,
        peak_type=peak.peak_type,
        pictures=[_picture_item(p) for p in peak.pictures],
    )


@router.get("/peaks", response_model=list[PeakListItem])
def list_peaks(
    q: str | None = Query(None),
    region: str | None = Query(None),
    has_pictures: bool | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    pic_count = func.count(Picture.id).label("picture_count")
    query = (
        db.query(Peak, pic_count)
        .outerjoin(Picture, Picture.peak_id == Peak.id)
        .group_by(Peak.id)
    )
    if q:
        query = query.filter(Peak.name.ilike(f"%{q}%"))
    if region:
        query = query.filter(Peak.region.ilike(f"%{region}%"))
    if has_pictures is True:
        query = query.having(pic_count > 0)
    elif has_pictures is False:
        query = query.having(pic_count == 0)
    query = query.order_by(Peak.elevation.desc()).offset(offset).limit(limit)

    return [
        PeakListItem(id=p.id, name=p.name, region=p.region, elevation=p.elevation, picture_count=cnt)
        for p, cnt in query.all()
    ]


@router.get("/peaks/{peak_id}", response_model=PeakDetail)
def get_peak(
    peak_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    return _peak_detail_response(_load_peak_detail(peak_id, db))


@router.patch("/peaks/{peak_id}", response_model=PeakDetail)
def update_peak(
    peak_id: int,
    body: PeakUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    peak = db.get(Peak, peak_id)
    if not peak:
        raise HTTPException(status_code=404, detail="Peak not found")
    if body.name is not None:
        peak.name = body.name.strip()
    if body.region is not None:
        peak.region = body.region.strip() or None
    db.commit()
    return _peak_detail_response(_load_peak_detail(peak_id, db))


@router.delete("/peaks/{peak_id}", status_code=204)
def delete_peak(
    peak_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    peak = (
        db.query(Peak)
        .options(joinedload(Peak.pictures))
        .filter(Peak.id == peak_id)
        .first()
    )
    if not peak:
        raise HTTPException(status_code=404, detail="Peak not found")
    uploader = PictureUploader(db)
    for pic in list(peak.pictures):
        uploader.remove_picture(pic)
    db.delete(peak)
    db.commit()


@router.delete("/pictures/{picture_id}", status_code=204)
def delete_picture(
    picture_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    pic = (
        db.query(Picture)
        .options(joinedload(Picture.author_rel), joinedload(Picture.license_rel))
        .filter(Picture.id == picture_id)
        .first()
    )
    if not pic:
        raise HTTPException(status_code=404, detail="Picture not found")
    uploader = PictureUploader(db)
    uploader.remove_picture(pic)
    db.commit()


@router.get("/peaks/{peak_id}/search-images", response_model=list[WikiResult])
def search_images(
    peak_id: int,
    q: str | None = Query(None),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    peak = db.get(Peak, peak_id)
    if not peak:
        raise HTTPException(status_code=404, detail="Peak not found")
    results = _wiki.search(q or peak.name, limit=8)
    return [
        WikiResult(
            filename=r.filename,
            title=r.title,
            direct_url=r.direct_url,
            source=r.source,
            author_name=r.author_name,
            author_url=r.author_url,
            license_name=r.license_name,
            license_url=r.license_url,
        )
        for r in results
    ]


@router.post("/peaks/{peak_id}/pictures", response_model=PictureItem, status_code=201)
def add_picture(
    peak_id: int,
    body: AddPictureRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    peak = db.get(Peak, peak_id)
    if not peak:
        raise HTTPException(status_code=404, detail="Peak not found")

    existing = db.query(func.count(Picture.id)).filter(Picture.peak_id == peak_id).scalar() or 0
    suffix = f"-{existing + 1}" if existing > 0 else ""
    public_id = f"peakquiz/{peak_id}{suffix}"

    uploader = PictureUploader(db)
    try:
        pic = uploader.add_picture(
            peak_id=peak_id,
            image_url=body.image_url,
            public_id=public_id,
            source=body.source,
            title=body.title,
            author_name=body.author_name,
            author_url=body.author_url,
            license_name=body.license_name,
            license_url=body.license_url,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

    if not pic:
        raise HTTPException(status_code=500, detail="Upload failed")

    db.commit()
    db.refresh(pic)
    if pic.author_id:
        db.refresh(pic.author_rel)
    if pic.license_id:
        db.refresh(pic.license_rel)
    return _picture_item(pic)
