from pydantic import BaseModel


class PictureItem(BaseModel):
    id: int
    cdn_url: str | None = None
    original_url: str
    title: str | None = None
    author_name: str | None = None
    author_url: str | None = None
    license_name: str | None = None
    license_url: str | None = None
    source: str | None = None


class PeakListItem(BaseModel):
    id: int
    name: str
    region: str | None = None
    elevation: int | None = None
    picture_count: int


class PeakDetail(BaseModel):
    id: int
    name: str
    region: str | None = None
    elevation: int | None = None
    mountain_range: str | None = None
    peak_type: str | None = None
    pictures: list[PictureItem]


class PeakUpdate(BaseModel):
    name: str | None = None
    region: str | None = None


class WikiResult(BaseModel):
    filename: str
    title: str
    direct_url: str
    source: str
    author_name: str | None = None
    author_url: str | None = None
    license_name: str | None = None
    license_url: str | None = None


class AddPictureRequest(BaseModel):
    image_url: str
    source: str | None = None
    title: str | None = None
    author_name: str | None = None
    author_url: str | None = None
    license_name: str | None = None
    license_url: str | None = None
