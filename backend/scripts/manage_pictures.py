"""
Manage peak pictures: upload to CDN, enrich metadata, find missing, or remove pictures.

Usage:
    uv run scripts/manage_pictures.py upload-missing [--dry-run]
    uv run scripts/manage_pictures.py find-missing
    uv run scripts/manage_pictures.py update-metadata [--dry-run]
    uv run scripts/manage_pictures.py manage-peak <name-or-id>
"""

import argparse
import io
import json
import re
import sys
import tempfile
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from dotenv import load_dotenv
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, joinedload

_backend_dir = Path(__file__).parent.parent
load_dotenv(_backend_dir / ".env")

sys.path.insert(0, str(_backend_dir))

from app.core.config import settings  # noqa: E402, I001
from app.db.models import Author, License, Peak, Picture  # noqa: E402

MAX_UPLOAD_BYTES = 10 * 1024 * 1024

_WIKI_DATEI_PREFIXES = (
    "https://de.wikipedia.org/wiki/Datei:",
    "https://en.wikipedia.org/wiki/File:",
    "https://commons.wikimedia.org/wiki/File:",
)

_HEADERS = {"User-Agent": "peakquiz-uploader/1.0 (stefan.schneider@wilmaa.com)"}


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _extract_author(html: str) -> tuple[str, str | None]:
    match = re.search(r'href="([^"]+)"', html)
    name = _strip_html(html)
    if not match:
        return name, None
    href = match.group(1)
    url = ("https:" + href) if href.startswith("//") else href
    return name, url


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


# ── Wikimedia metadata ────────────────────────────────────────────────────────

def _wiki_filename(url: str) -> str | None:
    if any(url.startswith(p) for p in _WIKI_DATEI_PREFIXES):
        return url.split(":")[-1]
    if url.startswith("https://upload.wikimedia.org/"):
        return urllib.parse.unquote(url.rstrip("/").split("/")[-1])
    return None


def _extmetadata(filename: str) -> dict:
    url = (
        "https://commons.wikimedia.org/w/api.php"
        f"?action=query&titles=File:{urllib.parse.quote(filename)}"
        "&prop=imageinfo&iiprop=extmetadata|url"
        "&iiextmetadatafilter=Artist|LicenseShortName|LicenseUrl"
        "&format=json"
    )
    data = _get(url)
    pages = data.get("query", {}).get("pages", {})
    page = next(iter(pages.values()), {})
    imageinfo = page.get("imageinfo", [{}])[0]
    return imageinfo.get("extmetadata", {})


def resolve_image_metadata(url: str) -> dict:
    filename = _wiki_filename(url)
    if not filename:
        return {"direct_url": url}

    file_data = _get(
        f"https://api.wikimedia.org/core/v1/commons/file/File:{urllib.parse.quote(filename)}"
    )
    direct_url = file_data.get("original", {}).get("url", url)

    meta = _extmetadata(filename)
    artist_html = meta.get("Artist", {}).get("value", "") or ""
    if artist_html:
        author_name, author_url = _extract_author(artist_html)
    else:
        author_name = file_data.get("latest", {}).get("user", {}).get("name", "") or ""
        author_url = None

    return {
        "direct_url": direct_url,
        "author_name": author_name or None,
        "author_url": author_url,
        "title": file_data.get("title", filename) or None,
        "source": f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(filename)}",
        "license_name": meta.get("LicenseShortName", {}).get("value") or None,
        "license_url": meta.get("LicenseUrl", {}).get("value") or None,
    }


# ── Wikimedia search ──────────────────────────────────────────────────────────

def search_wikimedia(peak_name: str, limit: int = 6) -> list[dict]:
    url = (
        "https://commons.wikimedia.org/w/api.php"
        "?action=query"
        "&generator=search"
        f"&gsrsearch={urllib.parse.quote(peak_name)}"
        "&gsrnamespace=6"
        f"&gsrlimit={limit}"
        "&prop=imageinfo"
        "&iiprop=url|extmetadata"
        "&iiextmetadatafilter=Artist|LicenseShortName|LicenseUrl"
        "&format=json"
    )
    try:
        data = _get(url)
    except Exception as e:
        print(f"    Search failed: {e}")
        return []

    pages = data.get("query", {}).get("pages", {})
    if not pages:
        return []

    candidates = []
    for page in pages.values():
        title = page.get("title", "")
        filename = title.removeprefix("File:")
        imageinfo = page.get("imageinfo", [{}])[0]
        direct_url = imageinfo.get("url", "")
        if not direct_url:
            continue

        meta = imageinfo.get("extmetadata", {})
        artist_html = meta.get("Artist", {}).get("value", "") or ""
        author_name, author_url = _extract_author(artist_html) if artist_html else (None, None)

        candidates.append({
            "filename": filename,
            "title": title,
            "direct_url": direct_url,
            "author_name": author_name or None,
            "author_url": author_url,
            "license_name": meta.get("LicenseShortName", {}).get("value") or None,
            "license_url": meta.get("LicenseUrl", {}).get("value") or None,
            "source": f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(filename)}",
        })

    return candidates


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_or_create_author(db: Session, name: str, url: str | None) -> Author:
    obj = db.query(Author).filter(Author.name == name).first()
    if obj:
        if url and not obj.url:
            obj.url = url
        return obj
    obj = Author(name=name, url=url)
    db.add(obj)
    db.flush()
    return obj


def get_or_create_license(db: Session, name: str, url: str | None) -> License:
    obj = db.query(License).filter(License.name == name).first()
    if obj:
        if url and not obj.url:
            obj.url = url
        return obj
    obj = License(name=name, url=url)
    db.add(obj)
    db.flush()
    return obj


# ── Image processing ──────────────────────────────────────────────────────────

def compress(data: bytes) -> bytes:
    img = Image.open(io.BytesIO(data)).convert("RGB")

    for quality in (95, 85, 75, 60):
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        if buf.tell() <= MAX_UPLOAD_BYTES:
            print(f"        ↓ compressed to {buf.tell() // 1024} KB (quality={quality})")
            return buf.getvalue()

    while True:
        img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75, optimize=True)
        if buf.tell() <= MAX_UPLOAD_BYTES:
            print(f"        ↓ scaled to {img.width}×{img.height}, {buf.tell() // 1024} KB")
            return buf.getvalue()


def upload_to_cloudinary(data: bytes, public_id: str) -> tuple[str, str] | None:
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        result = cloudinary.uploader.upload(tmp_path, public_id=public_id)
    except cloudinary.exceptions.BadRequest as e:
        print(f"  ✗ Upload failed: {e}")
        return None
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    cdn_url, _ = cloudinary_url(public_id, fetch_format="auto", quality="auto")
    return cdn_url, result["asset_id"]


def fetch_and_upload(image_url: str, public_id: str) -> tuple[str, str] | None:
    data = download(image_url)
    if len(data) > MAX_UPLOAD_BYTES:
        print(f"        ↓ {len(data) // 1024} KB — compressing…")
        data = compress(data)
    return upload_to_cloudinary(data, public_id)


# ── Modes ─────────────────────────────────────────────────────────────────────

def _apply_metadata(db: Session, pic: Picture, meta: dict) -> None:
    if meta.get("author_name") and not pic.author_id:
        author = get_or_create_author(db, meta["author_name"], meta.get("author_url"))
        pic.author_id = author.id
    if meta.get("license_name") and not pic.license_id:
        lic = get_or_create_license(db, meta["license_name"], meta.get("license_url"))
        pic.license_id = lic.id
    if not pic.author and meta.get("author_name"):
        pic.author = meta["author_name"]
    if not pic.title and meta.get("title"):
        pic.title = meta["title"]
    if not pic.source and meta.get("source"):
        pic.source = meta["source"]


def run_upload_missing(dry_run: bool, db: Session) -> None:
    pictures = (
        db.query(Picture)
        .filter(Picture.cdn_url.is_(None))
        .filter(Picture.original_url.isnot(None))
        .options(joinedload(Picture.peak))
        .all()
    )

    if not pictures:
        print("No pictures missing CDN URLs.")
        return

    print(f"Found {len(pictures)} picture(s) without CDN URL.")
    if dry_run:
        print("Dry run — no uploads will be performed.\n")

    ok = fail = 0
    for pic in pictures:
        peak_name = pic.peak.name if pic.peak else f"peak-{pic.peak_id}"
        public_id = f"peakquiz/{pic.peak_id}"
        print(f"  [{pic.id}] {peak_name}  →  {public_id}")

        if dry_run:
            continue

        try:
            meta = resolve_image_metadata(pic.original_url)
        except Exception as e:
            print(f"  ✗ Could not resolve URL: {e}")
            fail += 1
            continue

        upload = fetch_and_upload(meta["direct_url"], public_id)
        if upload is None:
            fail += 1
            continue

        cdn, asset_id = upload
        pic.cdn_url = cdn
        pic.cdn_asset_id = asset_id
        _apply_metadata(db, pic, meta)
        db.add(pic)
        db.commit()
        print(f"        ✓ {cdn}")
        ok += 1

    if not dry_run:
        print(f"\nDone — {ok} uploaded, {fail} failed.")


def run_find_missing(db: Session) -> None:
    peaks_without_pictures = (
        db.query(Peak)
        .outerjoin(Picture, Picture.peak_id == Peak.id)
        .filter(Picture.id.is_(None))
        .order_by(Peak.elevation.desc())
        .all()
    )

    if not peaks_without_pictures:
        print("Every peak already has at least one picture.")
        return

    print(f"Found {len(peaks_without_pictures)} peak(s) with no pictures.\n")

    saved = skipped = 0
    for peak in peaks_without_pictures:
        print(f"── {peak.name} ({peak.elevation} m, {peak.region}) ──")
        candidates = search_wikimedia(peak.name)

        if not candidates:
            print("   No results found on Wikimedia Commons.\n")
            continue

        accepted_for_peak = False
        for c in candidates:
            print(f"\n   Title  : {c['title']}")
            print(f"   Author : {c['author_name'] or '(unknown)'}", end="")
            print(f"  ({c['author_url']})" if c.get("author_url") else "")
            print(f"   License: {c['license_name'] or '(unknown)'}", end="")
            print(f"  ({c['license_url']})" if c.get("license_url") else "")
            print(f"   Source : {c['source']}")
            print(f"   URL    : {c['direct_url']}")

            answer = ""
            while answer not in ("y", "n", "o", "q"):
                answer = input("   Accept? [y]es / [n]o / [o]pen in browser / [q]uit peak  → ").strip().lower()
                if answer == "o":
                    webbrowser.open(c["source"])

            if answer == "q":
                print("   Skipping remaining results for this peak.")
                break

            if answer == "n":
                skipped += 1
                continue

            existing = db.query(Picture).filter(Picture.peak_id == peak.id).count()
            suffix = f"-{existing + 1}" if existing > 0 else ""
            public_id = f"peakquiz/{peak.id}{suffix}"
            print(f"   Uploading  →  {public_id} …")
            try:
                upload = fetch_and_upload(c["direct_url"], public_id)
            except Exception as e:
                print(f"   ✗ Failed: {e}")
                continue

            if upload is None:
                continue

            cdn, asset_id = upload

            author_id = None
            if c.get("author_name"):
                author_id = get_or_create_author(db, c["author_name"], c.get("author_url")).id

            license_id = None
            if c.get("license_name"):
                license_id = get_or_create_license(db, c["license_name"], c.get("license_url")).id

            pic = Picture(
                peak_id=peak.id,
                original_url=c["direct_url"],
                cdn_url=cdn,
                cdn_asset_id=asset_id,
                author=c.get("author_name"),
                source=c["source"],
                title=c["title"],
                author_id=author_id,
                license_id=license_id,
            )
            db.add(pic)
            db.commit()
            print(f"   ✓ Saved  {cdn}")
            saved += 1
            accepted_for_peak = True

            if accepted_for_peak:
                more = input("   Add another picture for this peak? [y/n]  → ").strip().lower()
                if more != "y":
                    break

        print()

    print(f"Done — {saved} picture(s) saved, {skipped} skipped.")


def run_update_metadata(dry_run: bool, db: Session) -> None:
    pictures = (
        db.query(Picture)
        .filter(Picture.original_url.isnot(None))
        .filter((Picture.author_id.is_(None)) | (Picture.license_id.is_(None)))
        .options(joinedload(Picture.peak))
        .all()
    )

    if not pictures:
        print("No pictures missing author/license data.")
        return

    print(f"Found {len(pictures)} picture(s) missing author or license data.")
    if dry_run:
        print("Dry run — no changes will be written.\n")

    ok = skipped = fail = 0
    for pic in pictures:
        peak_name = pic.peak.name if pic.peak else f"peak-{pic.peak_id}"
        print(f"  [{pic.id}] {peak_name}  ({pic.original_url[:60]}…)")

        filename = _wiki_filename(pic.original_url)
        if not filename:
            print("        ✗ Not a Wikimedia URL — skipping.")
            skipped += 1
            continue

        try:
            meta = resolve_image_metadata(pic.original_url)
        except Exception as e:
            print(f"        ✗ Metadata fetch failed: {e}")
            fail += 1
            continue

        changes = []
        if meta.get("author_name") and not pic.author_id:
            changes.append(f"author={meta['author_name']!r}")
        if meta.get("license_name") and not pic.license_id:
            changes.append(f"license={meta['license_name']!r}")
        if not pic.title and meta.get("title"):
            changes.append(f"title={meta['title']!r}")
        if not pic.source and meta.get("source"):
            changes.append("source=…")

        if not changes:
            print("        – already complete.")
            skipped += 1
            continue

        print(f"        → {', '.join(changes)}")
        if dry_run:
            continue

        _apply_metadata(db, pic, meta)
        db.add(pic)
        db.commit()
        ok += 1

    if not dry_run:
        print(f"\nDone — {ok} updated, {skipped} skipped, {fail} failed.")


def run_manage_peak(name_or_id: str, db: Session) -> None:
    """List and interactively delete pictures for a single peak."""
    # Resolve peak by ID or name substring
    peak: Peak | None = None
    if name_or_id.isdigit():
        peak = db.get(Peak, int(name_or_id))
    if peak is None:
        peak = (
            db.query(Peak)
            .filter(Peak.name.ilike(f"%{name_or_id}%"))
            .first()
        )
    if peak is None:
        print(f"No peak found matching {name_or_id!r}.")
        return

    pictures = (
        db.query(Picture)
        .filter(Picture.peak_id == peak.id)
        .options(joinedload(Picture.author_rel), joinedload(Picture.license_rel))
        .all()
    )

    print(f"\n── {peak.name} (id={peak.id}, {peak.elevation} m, {peak.region}) ──")
    if not pictures:
        print("  No pictures found.")
        return

    print(f"  {len(pictures)} picture(s):\n")

    deleted = 0
    for pic in pictures:
        author = pic.author_rel.name if pic.author_rel else pic.author or "(unknown)"
        license_ = pic.license_rel.name if pic.license_rel else "(unknown)"
        print(f"  [{pic.id}]")
        print(f"    CDN    : {pic.cdn_url or '(none)'}")
        print(f"    Source : {pic.original_url}")
        print(f"    Author : {author}")
        print(f"    License: {license_}")
        if pic.title:
            print(f"    Title  : {pic.title}")

        answer = ""
        while answer not in ("k", "d", "o"):
            answer = input("    Action? [k]eep / [d]elete / [o]pen in browser  → ").strip().lower()
            if answer == "o":
                url = pic.source or pic.cdn_url or pic.original_url
                if url:
                    webbrowser.open(url)

        if answer == "d":
            if pic.cdn_url and pic.cdn_asset_id:
                try:
                    cloudinary.uploader.destroy(pic.cdn_asset_id, resource_type="image")
                    print("    ✓ Removed from Cloudinary.")
                except Exception as e:
                    print(f"    ✗ Cloudinary deletion failed: {e}")
            db.delete(pic)
            db.commit()
            print("    ✓ Deleted from database.")
            deleted += 1
        else:
            print("    – Kept.")
        print()

    print(f"Done — {deleted} picture(s) deleted, {len(pictures) - deleted} kept.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Manage peak pictures")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_upload = sub.add_parser("upload-missing", help="Upload pictures missing a CDN URL")
    p_upload.add_argument("--dry-run", action="store_true")

    sub.add_parser("find-missing", help="Search Wikimedia for peaks with no pictures")

    p_meta = sub.add_parser("update-metadata", help="Fetch author/license for pictures missing it")
    p_meta.add_argument("--dry-run", action="store_true")

    p_manage = sub.add_parser("manage-peak", help="List and remove pictures for a single peak")
    p_manage.add_argument("peak", help="Peak name (partial match) or numeric ID")

    args = parser.parse_args()

    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )

    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})

    with Session(engine) as db:
        if args.mode == "upload-missing":
            run_upload_missing(dry_run=args.dry_run, db=db)
        elif args.mode == "find-missing":
            run_find_missing(db=db)
        elif args.mode == "update-metadata":
            run_update_metadata(dry_run=args.dry_run, db=db)
        elif args.mode == "manage-peak":
            run_manage_peak(name_or_id=args.peak, db=db)


if __name__ == "__main__":
    main()
