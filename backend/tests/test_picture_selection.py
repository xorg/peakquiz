from app.db.models import Peak, Picture


def _seed_multi_picture_peak(db, n_pictures: int) -> tuple:
    """Create one peak with n_pictures CDN images plus 3 single-picture filler peaks."""
    peak = Peak(name="Multi Peak", elevation=4000, region="Switzerland")
    db.add(peak)
    db.flush()
    for i in range(n_pictures):
        db.add(Picture(
            peak_id=peak.id,
            original_url=f"http://example.com/multi{i}.jpg",
            cdn_url=f"https://res.cloudinary.com/test/image/upload/f_auto,q_auto/multi{i}",
        ))

    # Need at least 4 peaks total for the quiz to start
    fillers = []
    for i in range(3):
        filler = Peak(name=f"Filler Peak {i}", elevation=3000, region="Switzerland")
        db.add(filler)
        db.flush()
        db.add(Picture(
            peak_id=filler.id,
            original_url=f"http://example.com/filler{i}.jpg",
            cdn_url=f"https://res.cloudinary.com/test/image/upload/f_auto,q_auto/filler{i}",
        ))
        fillers.append(filler)

    db.commit()
    return peak, fillers


def _image_urls_for_peak(client, peak_name: str, runs: int) -> set:
    """Start the quiz `runs` times and collect all imageUrls seen for the given peak name."""
    urls = set()
    for _ in range(runs):
        session = client.post("/api/quiz/start").json()
        for q in session["questions"]:
            if q["peak"]["name"] == peak_name:
                urls.add(q["peak"]["imageUrl"])
    return urls


class TestPictureRotation:
    RUNS = 30  # enough attempts to expect all pictures to appear at least once

    def test_two_pictures_both_shown(self, client, db):
        peak, _ = _seed_multi_picture_peak(db, n_pictures=2)
        urls = _image_urls_for_peak(client, peak.name, self.RUNS)
        assert len(urls) == 2, (
            f"Expected both pictures to appear across {self.RUNS} runs, "
            f"but only saw: {urls}"
        )

    def test_three_pictures_all_shown(self, client, db):
        peak, _ = _seed_multi_picture_peak(db, n_pictures=3)
        urls = _image_urls_for_peak(client, peak.name, self.RUNS)
        assert len(urls) == 3, (
            f"Expected all 3 pictures to appear across {self.RUNS} runs, "
            f"but only saw: {urls}"
        )
