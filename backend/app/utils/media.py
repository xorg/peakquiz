"""Cloudinary media manager for peak pictures."""

import io
import re
import tempfile
import urllib.request
from pathlib import Path

import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from PIL import Image
from sqlalchemy.orm import Session

from ..db.models import Author, License, Picture

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
_HEADERS = {"User-Agent": "peakquiz/1.0"}


class PictureUploader:
    def __init__(self, db: Session) -> None:
        self._db = db

    # ── HTTP ──────────────────────────────────────────────────────────────────

    def _download(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()

    # ── Image processing ──────────────────────────────────────────────────────

    def _compress(self, data: bytes) -> bytes:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        for quality in (95, 85, 75, 60):
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            if buf.tell() <= MAX_UPLOAD_BYTES:
                return buf.getvalue()
        while True:
            img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=75, optimize=True)
            if buf.tell() <= MAX_UPLOAD_BYTES:
                return buf.getvalue()

    # ── Cloudinary ────────────────────────────────────────────────────────────

    @staticmethod
    def _public_id_from_cdn_url(cdn_url: str) -> str | None:
        match = re.search(r"/(peakquiz/[^.?]+)", cdn_url)
        return match.group(1) if match else None

    def _upload(self, data: bytes, public_id: str) -> tuple[str, str] | None:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            result = cloudinary.uploader.upload(tmp_path, public_id=public_id)
        except Exception:
            return None
        finally:
            Path(tmp_path).unlink(missing_ok=True)
        cdn_url, _ = cloudinary_url(public_id, fetch_format="auto", quality="auto")
        return cdn_url, result["asset_id"]

    def _delete_from_cloudinary(self, cdn_url: str) -> bool:
        public_id = self._public_id_from_cdn_url(cdn_url)
        if not public_id:
            return False
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get("result") == "ok"
        except Exception:
            return False

    # ── DB helpers ────────────────────────────────────────────────────────────

    def _get_or_create_author(self, name: str, url: str | None) -> Author:
        obj = self._db.query(Author).filter(Author.name == name).first()
        if obj:
            if url and not obj.url:
                obj.url = url
            return obj
        obj = Author(name=name, url=url)
        self._db.add(obj)
        self._db.flush()
        return obj

    def _get_or_create_license(self, name: str, url: str | None) -> License:
        obj = self._db.query(License).filter(License.name == name).first()
        if obj:
            if url and not obj.url:
                obj.url = url
            return obj
        obj = License(name=name, url=url)
        self._db.add(obj)
        self._db.flush()
        return obj

    # ── Public API ────────────────────────────────────────────────────────────

    def add_picture(
        self,
        peak_id: int,
        image_url: str,
        public_id: str,
        *,
        source: str | None = None,
        title: str | None = None,
        author_name: str | None = None,
        author_url: str | None = None,
        license_name: str | None = None,
        license_url: str | None = None,
    ) -> Picture | None:
        data = self._download(image_url)
        if len(data) > MAX_UPLOAD_BYTES:
            data = self._compress(data)
        result = self._upload(data, public_id)
        if not result:
            return None
        cdn_url, asset_id = result

        author = self._get_or_create_author(author_name, author_url) if author_name else None
        license_obj = self._get_or_create_license(license_name, license_url) if license_name else None

        pic = Picture(
            peak_id=peak_id,
            original_url=image_url,
            cdn_url=cdn_url,
            cdn_asset_id=asset_id,
            source=source,
            title=title,
            author=author_name,
            author_id=author.id if author else None,
            license_id=license_obj.id if license_obj else None,
        )
        self._db.add(pic)
        self._db.flush()
        return pic

    def remove_picture(self, pic: Picture) -> None:
        if pic.cdn_url:
            self._delete_from_cloudinary(pic.cdn_url)
        self._db.delete(pic)
