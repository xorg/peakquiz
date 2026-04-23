"""Tests for admin API routes: access control, CRUD, Wikimedia search, picture upload."""

from unittest.mock import MagicMock, patch

import pytest

from app.api.routes.auth import get_current_user
from app.db.models import Author, License, Peak, Picture, User
from app.main import app
from app.utils.media import PictureUploader
from app.utils.wikimedia import WikiImage, WikimediaClient

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def admin_user(db):
    user = User(id="admin-1", username="Admin", is_admin=True)
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def regular_user(db):
    user = User(id="regular-1", username="Regular", is_admin=False)
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def admin_client(client, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user
    yield client


@pytest.fixture
def regular_client(client, regular_user):
    app.dependency_overrides[get_current_user] = lambda: regular_user
    yield client


@pytest.fixture
def peak(db):
    """One peak with a picture that has author + license."""
    author = Author(name="Axel Photographer", url="https://example.com/axel")
    lic = License(name="CC BY-SA 4.0", url="https://creativecommons.org/licenses/by-sa/4.0/")
    db.add_all([author, lic])
    db.flush()

    p = Peak(name="Matterhorn", elevation=4478, region="Valais", mountain_range="Pennine Alps")
    db.add(p)
    db.flush()
    db.add(Picture(
        peak_id=p.id,
        original_url="http://example.com/matterhorn.jpg",
        cdn_url="https://res.cloudinary.com/test/image/upload/f_auto,q_auto/peakquiz/1",
        title="Matterhorn south face",
        author=author.name,
        author_id=author.id,
        license_id=lic.id,
        source="https://commons.wikimedia.org/wiki/File:Matterhorn.jpg",
    ))
    db.commit()
    return p


@pytest.fixture
def peak_no_pics(db):
    """A peak with no pictures."""
    p = Peak(name="Eiger", elevation=3967, region="Bern")
    db.add(p)
    db.commit()
    return p


@pytest.fixture
def fake_wiki_results():
    return [
        WikiImage(
            filename="Eiger_north_face.jpg",
            title="File:Eiger_north_face.jpg",
            direct_url="https://upload.wikimedia.org/eiger.jpg",
            source="https://commons.wikimedia.org/wiki/File:Eiger_north_face.jpg",
            author_name="Hans Photo",
            author_url="https://commons.wikimedia.org/wiki/User:Hans",
            license_name="CC BY 3.0",
            license_url="https://creativecommons.org/licenses/by/3.0/",
        ),
    ]


# ── Access control ────────────────────────────────────────────────────────────


class TestAdminAccess:
    def test_unauthenticated_returns_401(self, client, peak):
        assert client.get("/api/admin/peaks").status_code == 401

    def test_non_admin_returns_403(self, regular_client, peak):
        assert regular_client.get("/api/admin/peaks").status_code == 403

    def test_admin_can_access_peaks(self, admin_client, peak):
        assert admin_client.get("/api/admin/peaks").status_code == 200


# ── List peaks ────────────────────────────────────────────────────────────────


class TestListPeaks:
    def test_returns_all_peaks_with_picture_count(self, admin_client, peak, peak_no_pics):
        data = admin_client.get("/api/admin/peaks").json()
        by_id = {p["id"]: p for p in data}

        assert by_id[peak.id]["picture_count"] == 1
        assert by_id[peak_no_pics.id]["picture_count"] == 0

    def test_includes_name_region_elevation(self, admin_client, peak):
        data = admin_client.get("/api/admin/peaks").json()
        row = next(p for p in data if p["id"] == peak.id)
        assert row["name"] == "Matterhorn"
        assert row["region"] == "Valais"
        assert row["elevation"] == 4478

    def test_search_filters_by_name(self, admin_client, peak, peak_no_pics):
        data = admin_client.get("/api/admin/peaks?q=matter").json()
        names = [p["name"] for p in data]
        assert "Matterhorn" in names
        assert "Eiger" not in names

    def test_search_is_case_insensitive(self, admin_client, peak):
        data = admin_client.get("/api/admin/peaks?q=MATTER").json()
        assert any(p["name"] == "Matterhorn" for p in data)

    def test_region_filter(self, admin_client, peak, peak_no_pics):
        data = admin_client.get("/api/admin/peaks?region=Valais").json()
        assert all(p["region"] == "Valais" for p in data)
        assert not any(p["name"] == "Eiger" for p in data)

    def test_has_pictures_true_excludes_pictureless_peaks(self, admin_client, peak, peak_no_pics):
        data = admin_client.get("/api/admin/peaks?has_pictures=true").json()
        assert all(p["picture_count"] > 0 for p in data)
        assert not any(p["name"] == "Eiger" for p in data)

    def test_has_pictures_false_excludes_peaks_with_pictures(self, admin_client, peak, peak_no_pics):
        data = admin_client.get("/api/admin/peaks?has_pictures=false").json()
        assert all(p["picture_count"] == 0 for p in data)
        assert not any(p["name"] == "Matterhorn" for p in data)

    def test_limit_caps_results(self, admin_client, db):
        for i in range(5):
            db.add(Peak(name=f"Limit Peak {i}", elevation=3000 + i))
        db.commit()
        data = admin_client.get("/api/admin/peaks?limit=3").json()
        assert len(data) <= 3

    def test_offset_skips_results(self, admin_client, db):
        for i in range(4):
            db.add(Peak(name=f"Offset Peak {i}", elevation=4000 - i))
        db.commit()
        all_data = admin_client.get("/api/admin/peaks?limit=200").json()
        offset_data = admin_client.get("/api/admin/peaks?limit=200&offset=2").json()
        assert len(offset_data) == len(all_data) - 2
        assert offset_data[0]["id"] == all_data[2]["id"]


# ── Create peak ───────────────────────────────────────────────────────────────


class TestCreatePeak:
    def test_creates_peak_with_required_name(self, admin_client, db):
        resp = admin_client.post("/api/admin/peaks", json={"name": "Jungfrau"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Jungfrau"
        assert db.query(Peak).filter(Peak.name == "Jungfrau").first() is not None

    def test_creates_peak_with_all_fields(self, admin_client, db):
        resp = admin_client.post("/api/admin/peaks", json={
            "name": "Finsteraarhorn",
            "region": "Bern",
            "elevation": 4274,
            "mountain_range": "Bernese Alps",
            "peak_type": "Hauptgipfel",
        })
        assert resp.status_code == 201
        p = db.query(Peak).filter(Peak.name == "Finsteraarhorn").first()
        assert p.region == "Bern"
        assert p.elevation == 4274
        assert p.mountain_range == "Bernese Alps"
        assert p.peak_type == "Hauptgipfel"

    def test_response_includes_empty_pictures_list(self, admin_client):
        resp = admin_client.post("/api/admin/peaks", json={"name": "Weisshorn"})
        assert resp.json()["pictures"] == []

    def test_name_stripped_of_whitespace(self, admin_client, db):
        admin_client.post("/api/admin/peaks", json={"name": "  Tödi  "})
        assert db.query(Peak).filter(Peak.name == "Tödi").first() is not None

    def test_empty_name_returns_400(self, admin_client):
        assert admin_client.post("/api/admin/peaks", json={"name": "   "}).status_code == 400

    def test_duplicate_name_returns_409(self, admin_client, peak):
        resp = admin_client.post("/api/admin/peaks", json={"name": "Matterhorn"})
        assert resp.status_code == 409

    def test_requires_admin(self, regular_client):
        assert regular_client.post("/api/admin/peaks", json={"name": "X"}).status_code == 403


# ── Get peak detail ───────────────────────────────────────────────────────────


class TestGetPeak:
    def test_returns_peak_fields(self, admin_client, peak):
        data = admin_client.get(f"/api/admin/peaks/{peak.id}").json()
        assert data["name"] == "Matterhorn"
        assert data["elevation"] == 4478
        assert data["region"] == "Valais"
        assert data["mountain_range"] == "Pennine Alps"

    def test_returns_pictures_list(self, admin_client, peak):
        data = admin_client.get(f"/api/admin/peaks/{peak.id}").json()
        assert len(data["pictures"]) == 1
        pic = data["pictures"][0]
        assert pic["title"] == "Matterhorn south face"
        assert "cloudinary.com" in pic["cdn_url"]

    def test_picture_includes_author_and_license(self, admin_client, peak):
        data = admin_client.get(f"/api/admin/peaks/{peak.id}").json()
        pic = data["pictures"][0]
        assert pic["author_name"] == "Axel Photographer"
        assert pic["author_url"] == "https://example.com/axel"
        assert pic["license_name"] == "CC BY-SA 4.0"
        assert pic["license_url"] == "https://creativecommons.org/licenses/by-sa/4.0/"

    def test_unknown_peak_returns_404(self, admin_client):
        assert admin_client.get("/api/admin/peaks/99999").status_code == 404

    def test_peak_with_no_pictures_returns_empty_list(self, admin_client, peak_no_pics):
        data = admin_client.get(f"/api/admin/peaks/{peak_no_pics.id}").json()
        assert data["pictures"] == []


# ── Update peak ───────────────────────────────────────────────────────────────


class TestUpdatePeak:
    def test_update_name(self, admin_client, peak, db):
        resp = admin_client.patch(f"/api/admin/peaks/{peak.id}", json={"name": "Monte Cervino"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Monte Cervino"
        db.refresh(peak)
        assert peak.name == "Monte Cervino"

    def test_update_region(self, admin_client, peak, db):
        resp = admin_client.patch(f"/api/admin/peaks/{peak.id}", json={"region": "Aosta Valley"})
        assert resp.status_code == 200
        assert resp.json()["region"] == "Aosta Valley"
        db.refresh(peak)
        assert peak.region == "Aosta Valley"

    def test_empty_region_clears_to_null(self, admin_client, peak, db):
        resp = admin_client.patch(f"/api/admin/peaks/{peak.id}", json={"region": ""})
        assert resp.status_code == 200
        assert resp.json()["region"] is None
        db.refresh(peak)
        assert peak.region is None

    def test_name_stripped_of_whitespace(self, admin_client, peak, db):
        admin_client.patch(f"/api/admin/peaks/{peak.id}", json={"name": "  Matterhorn  "})
        db.refresh(peak)
        assert peak.name == "Matterhorn"

    def test_response_includes_pictures(self, admin_client, peak):
        resp = admin_client.patch(f"/api/admin/peaks/{peak.id}", json={"name": "X"})
        assert "pictures" in resp.json()
        assert len(resp.json()["pictures"]) == 1

    def test_unknown_peak_returns_404(self, admin_client):
        assert admin_client.patch("/api/admin/peaks/99999", json={"name": "X"}).status_code == 404


# ── Delete peak ───────────────────────────────────────────────────────────────


class TestDeletePeak:
    @patch("cloudinary.uploader.destroy")
    def test_removes_peak_from_db(self, mock_destroy, admin_client, peak, db):
        peak_id = peak.id
        resp = admin_client.delete(f"/api/admin/peaks/{peak_id}")
        assert resp.status_code == 204
        assert db.get(Peak, peak_id) is None

    @patch("cloudinary.uploader.destroy")
    def test_removes_pictures_from_db(self, mock_destroy, admin_client, peak, db):
        pic_id = peak.pictures[0].id
        admin_client.delete(f"/api/admin/peaks/{peak.id}")
        assert db.get(Picture, pic_id) is None

    @patch("cloudinary.uploader.destroy")
    def test_calls_cloudinary_destroy_for_cdn_picture(self, mock_destroy, admin_client, peak):
        admin_client.delete(f"/api/admin/peaks/{peak.id}")
        mock_destroy.assert_called_once_with("peakquiz/1")

    @patch("cloudinary.uploader.destroy")
    def test_peak_without_cdn_pictures_skips_cloudinary(self, mock_destroy, admin_client, peak_no_pics):
        admin_client.delete(f"/api/admin/peaks/{peak_no_pics.id}")
        mock_destroy.assert_not_called()

    def test_unknown_peak_returns_404(self, admin_client):
        assert admin_client.delete("/api/admin/peaks/99999").status_code == 404


# ── Delete picture ────────────────────────────────────────────────────────────


class TestDeletePicture:
    @patch("cloudinary.uploader.destroy")
    def test_removes_picture_from_db(self, mock_destroy, admin_client, peak, db):
        pic_id = peak.pictures[0].id
        resp = admin_client.delete(f"/api/admin/pictures/{pic_id}")
        assert resp.status_code == 204
        assert db.get(Picture, pic_id) is None

    @patch("cloudinary.uploader.destroy")
    def test_calls_cloudinary_destroy(self, mock_destroy, admin_client, peak):
        pic_id = peak.pictures[0].id
        admin_client.delete(f"/api/admin/pictures/{pic_id}")
        mock_destroy.assert_called_once_with("peakquiz/1")

    @patch("cloudinary.uploader.destroy")
    def test_peak_still_exists_after_picture_delete(self, mock_destroy, admin_client, peak, db):
        pic_id = peak.pictures[0].id
        admin_client.delete(f"/api/admin/pictures/{pic_id}")
        assert db.get(Peak, peak.id) is not None

    def test_unknown_picture_returns_404(self, admin_client):
        assert admin_client.delete("/api/admin/pictures/99999").status_code == 404

    @patch("cloudinary.uploader.destroy")
    def test_picture_without_cdn_url_skips_cloudinary(self, mock_destroy, admin_client, peak_no_pics, db):
        pic = Picture(
            peak_id=peak_no_pics.id,
            original_url="http://example.com/no-cdn.jpg",
            cdn_url=None,
        )
        db.add(pic)
        db.commit()
        admin_client.delete(f"/api/admin/pictures/{pic.id}")
        mock_destroy.assert_not_called()


# ── Search images (Wikimedia) ─────────────────────────────────────────────────


class TestSearchImages:
    def test_uses_peak_name_when_no_query(self, admin_client, peak, fake_wiki_results):
        with patch.object(WikimediaClient, "search", return_value=fake_wiki_results) as mock_search:
            admin_client.get(f"/api/admin/peaks/{peak.id}/search-images")
            mock_search.assert_called_once_with("Matterhorn", limit=8)

    def test_uses_custom_query_when_provided(self, admin_client, peak, fake_wiki_results):
        with patch.object(WikimediaClient, "search", return_value=fake_wiki_results) as mock_search:
            admin_client.get(f"/api/admin/peaks/{peak.id}/search-images?q=matterhorn+summer")
            mock_search.assert_called_once_with("matterhorn summer", limit=8)

    def test_returns_wiki_result_fields(self, admin_client, peak, fake_wiki_results):
        with patch.object(WikimediaClient, "search", return_value=fake_wiki_results):
            data = admin_client.get(f"/api/admin/peaks/{peak.id}/search-images").json()
        assert len(data) == 1
        r = data[0]
        assert r["filename"] == "Eiger_north_face.jpg"
        assert r["direct_url"] == "https://upload.wikimedia.org/eiger.jpg"
        assert r["author_name"] == "Hans Photo"
        assert r["license_name"] == "CC BY 3.0"

    def test_empty_results_returned_as_empty_list(self, admin_client, peak):
        with patch.object(WikimediaClient, "search", return_value=[]):
            data = admin_client.get(f"/api/admin/peaks/{peak.id}/search-images").json()
        assert data == []

    def test_unknown_peak_returns_404(self, admin_client):
        assert admin_client.get("/api/admin/peaks/99999/search-images").status_code == 404


# ── Add picture ───────────────────────────────────────────────────────────────


_FAKE_CDN = "https://res.cloudinary.com/test/image/upload/f_auto,q_auto/peakquiz/99"
_FAKE_ASSET_ID = "asset-abc-123"


@pytest.fixture
def mock_uploader():
    """Patch PictureUploader internals so no real HTTP or Cloudinary calls are made."""
    with (
        patch.object(PictureUploader, "_download", return_value=b"fake_image_data"),
        patch.object(PictureUploader, "_upload", return_value=(_FAKE_CDN, _FAKE_ASSET_ID)),
    ):
        yield


class TestAddPicture:
    def test_creates_picture_record(self, admin_client, peak_no_pics, db, mock_uploader):
        resp = admin_client.post(f"/api/admin/peaks/{peak_no_pics.id}/pictures", json={
            "image_url": "https://upload.wikimedia.org/eiger.jpg",
            "title": "Eiger north face",
        })
        assert resp.status_code == 201
        pic = db.query(Picture).filter(Picture.peak_id == peak_no_pics.id).first()
        assert pic is not None
        assert pic.cdn_url == _FAKE_CDN
        assert pic.title == "Eiger north face"

    def test_first_picture_uses_base_public_id(self, admin_client, peak_no_pics, mock_uploader):
        with patch.object(PictureUploader, "_upload", return_value=(_FAKE_CDN, _FAKE_ASSET_ID)) as mock_upload:
            admin_client.post(f"/api/admin/peaks/{peak_no_pics.id}/pictures", json={
                "image_url": "https://upload.wikimedia.org/eiger.jpg",
            })
            args, _ = mock_upload.call_args
            assert args[1] == f"peakquiz/{peak_no_pics.id}"

    def test_second_picture_uses_suffixed_public_id(self, admin_client, peak, mock_uploader):
        # peak already has 1 picture
        with patch.object(PictureUploader, "_upload", return_value=(_FAKE_CDN, _FAKE_ASSET_ID)) as mock_upload:
            admin_client.post(f"/api/admin/peaks/{peak.id}/pictures", json={
                "image_url": "https://upload.wikimedia.org/eiger.jpg",
            })
            args, _ = mock_upload.call_args
            assert args[1] == f"peakquiz/{peak.id}-2"

    def test_creates_author_record(self, admin_client, peak_no_pics, db, mock_uploader):
        admin_client.post(f"/api/admin/peaks/{peak_no_pics.id}/pictures", json={
            "image_url": "https://upload.wikimedia.org/eiger.jpg",
            "author_name": "New Author",
            "author_url": "https://example.com/author",
        })
        author = db.query(Author).filter(Author.name == "New Author").first()
        assert author is not None
        assert author.url == "https://example.com/author"

    def test_creates_license_record(self, admin_client, peak_no_pics, db, mock_uploader):
        admin_client.post(f"/api/admin/peaks/{peak_no_pics.id}/pictures", json={
            "image_url": "https://upload.wikimedia.org/eiger.jpg",
            "license_name": "CC BY 4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
        })
        lic = db.query(License).filter(License.name == "CC BY 4.0").first()
        assert lic is not None
        assert lic.url == "https://creativecommons.org/licenses/by/4.0/"

    def test_reuses_existing_author(self, admin_client, peak, peak_no_pics, db, mock_uploader):
        # peak already has author "Axel Photographer"; adding to peak_no_pics with same name
        admin_client.post(f"/api/admin/peaks/{peak_no_pics.id}/pictures", json={
            "image_url": "https://upload.wikimedia.org/eiger.jpg",
            "author_name": "Axel Photographer",
        })
        count = db.query(Author).filter(Author.name == "Axel Photographer").count()
        assert count == 1

    def test_response_contains_picture_fields(self, admin_client, peak_no_pics, mock_uploader):
        resp = admin_client.post(f"/api/admin/peaks/{peak_no_pics.id}/pictures", json={
            "image_url": "https://upload.wikimedia.org/eiger.jpg",
            "title": "North Face",
            "author_name": "Photographer",
            "license_name": "CC BY 3.0",
        })
        data = resp.json()
        assert data["cdn_url"] == _FAKE_CDN
        assert data["title"] == "North Face"
        assert data["author_name"] == "Photographer"
        assert data["license_name"] == "CC BY 3.0"

    def test_unknown_peak_returns_404(self, admin_client):
        assert admin_client.post("/api/admin/peaks/99999/pictures", json={
            "image_url": "https://upload.wikimedia.org/eiger.jpg",
        }).status_code == 404

    def test_upload_failure_returns_500(self, admin_client, peak_no_pics):
        with (
            patch.object(PictureUploader, "_download", return_value=b"data"),
            patch.object(PictureUploader, "_upload", return_value=None),
        ):
            resp = admin_client.post(f"/api/admin/peaks/{peak_no_pics.id}/pictures", json={
                "image_url": "https://upload.wikimedia.org/eiger.jpg",
            })
        assert resp.status_code == 500

    def test_download_error_returns_500(self, admin_client, peak_no_pics):
        with patch.object(PictureUploader, "_download", side_effect=Exception("network error")):
            resp = admin_client.post(f"/api/admin/peaks/{peak_no_pics.id}/pictures", json={
                "image_url": "https://upload.wikimedia.org/eiger.jpg",
            })
        assert resp.status_code == 500
