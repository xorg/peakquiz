"""Wikimedia Commons client for searching and fetching image metadata."""

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field


@dataclass
class WikiImage:
    filename: str
    title: str
    direct_url: str
    source: str
    author_name: str | None = None
    author_url: str | None = None
    license_name: str | None = None
    license_url: str | None = None


class WikimediaClient:
    API_BASE = "https://commons.wikimedia.org/w/api.php"
    CORE_BASE = "https://api.wikimedia.org/core/v1/commons"
    HEADERS: dict = field(default_factory=dict)

    _WIKI_PREFIXES = (
        "https://de.wikipedia.org/wiki/Datei:",
        "https://en.wikipedia.org/wiki/File:",
        "https://commons.wikimedia.org/wiki/File:",
    )

    def __init__(self, user_agent: str = "peakquiz/1.0") -> None:
        self._headers = {"User-Agent": user_agent}

    # ── HTTP ──────────────────────────────────────────────────────────────────

    def _get(self, url: str) -> dict:
        req = urllib.request.Request(url, headers=self._headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())

    # ── Parsing helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _strip_html(text: str) -> str:
        return re.sub(r"<[^>]+>", "", text).strip()

    @classmethod
    def _parse_author(cls, html: str) -> tuple[str, str | None]:
        match = re.search(r'href="([^"]+)"', html)
        name = cls._strip_html(html)
        if not match:
            return name, None
        href = match.group(1)
        return name, ("https:" + href) if href.startswith("//") else href

    def _filename_from_url(self, url: str) -> str | None:
        if any(url.startswith(p) for p in self._WIKI_PREFIXES):
            return url.split(":")[-1]
        if url.startswith("https://upload.wikimedia.org/"):
            return urllib.parse.unquote(url.rstrip("/").split("/")[-1])
        return None

    def _extmetadata(self, filename: str) -> dict:
        url = (
            f"{self.API_BASE}?action=query&titles=File:{urllib.parse.quote(filename)}"
            "&prop=imageinfo&iiprop=extmetadata|url"
            "&iiextmetadatafilter=Artist|LicenseShortName|LicenseUrl&format=json"
        )
        pages = self._get(url).get("query", {}).get("pages", {})
        imageinfo = next(iter(pages.values()), {}).get("imageinfo", [{}])[0]
        return imageinfo.get("extmetadata", {})

    def _image_from_extmeta(self, filename: str, direct_url: str, meta: dict) -> WikiImage:
        artist_html = meta.get("Artist", {}).get("value", "") or ""
        if artist_html:
            author_name, author_url = self._parse_author(artist_html)
        else:
            author_name, author_url = None, None
        return WikiImage(
            filename=filename,
            title=f"File:{filename}",
            direct_url=direct_url,
            source=f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(filename)}",
            author_name=author_name or None,
            author_url=author_url,
            license_name=meta.get("LicenseShortName", {}).get("value") or None,
            license_url=meta.get("LicenseUrl", {}).get("value") or None,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def search(self, query: str, limit: int = 6) -> list[WikiImage]:
        """Search Wikimedia Commons (File namespace) for images matching query."""
        url = (
            f"{self.API_BASE}?action=query&generator=search"
            f"&gsrsearch={urllib.parse.quote(query)}&gsrnamespace=6"
            f"&gsrlimit={limit}&prop=imageinfo&iiprop=url|extmetadata"
            "&iiextmetadatafilter=Artist|LicenseShortName|LicenseUrl&format=json"
        )
        try:
            data = self._get(url)
        except Exception:
            return []

        results = []
        for page in data.get("query", {}).get("pages", {}).values():
            title = page.get("title", "")
            filename = title.removeprefix("File:")
            imageinfo = page.get("imageinfo", [{}])[0]
            direct_url = imageinfo.get("url", "")
            if not direct_url:
                continue
            meta = imageinfo.get("extmetadata", {})
            results.append(self._image_from_extmeta(filename, direct_url, meta))
        return results

    def resolve(self, url: str) -> WikiImage | None:
        """Resolve a Wikimedia file-page or upload URL to a WikiImage with metadata."""
        filename = self._filename_from_url(url)
        if not filename:
            return None
        try:
            file_data = self._get(
                f"{self.CORE_BASE}/file/File:{urllib.parse.quote(filename)}"
            )
        except Exception:
            return None
        direct_url = file_data.get("original", {}).get("url", url)
        meta = self._extmetadata(filename)
        image = self._image_from_extmeta(filename, direct_url, meta)
        if not image.author_name:
            image.author_name = (
                file_data.get("latest", {}).get("user", {}).get("name") or None
            )
        image.title = file_data.get("title", image.title) or image.title
        return image
