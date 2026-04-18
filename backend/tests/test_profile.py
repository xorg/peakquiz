import pytest
from app.db.models import Guess


def add_guesses(db, user_id: str, peak_id: int, correct: int, wrong: int):
    for _ in range(correct):
        db.add(Guess(user_id=user_id, peak_id=peak_id, is_correct=True))
    for _ in range(wrong):
        db.add(Guess(user_id=user_id, peak_id=peak_id, is_correct=False))
    db.commit()


class TestProfileStats:
    def test_requires_authentication(self, client):
        resp = client.get("/api/profile/stats")
        assert resp.status_code == 401

    def test_empty_stats_for_new_user(self, auth_client):
        data = auth_client.get("/api/profile/stats").json()
        assert data["totalGuesses"] == 0
        assert data["correctGuesses"] == 0
        assert data["accuracyPercent"] == 0.0
        assert data["troublePeaks"] == []

    def test_total_and_correct_counts(self, auth_client, auth_user, peaks, db):
        add_guesses(db, auth_user.id, peaks[0].id, correct=3, wrong=2)
        add_guesses(db, auth_user.id, peaks[1].id, correct=1, wrong=0)

        data = auth_client.get("/api/profile/stats").json()
        assert data["totalGuesses"] == 6
        assert data["correctGuesses"] == 4

    def test_accuracy_percent(self, auth_client, auth_user, peaks, db):
        add_guesses(db, auth_user.id, peaks[0].id, correct=1, wrong=3)

        data = auth_client.get("/api/profile/stats").json()
        assert data["accuracyPercent"] == 25.0

    def test_perfect_accuracy(self, auth_client, auth_user, peaks, db):
        add_guesses(db, auth_user.id, peaks[0].id, correct=5, wrong=0)

        data = auth_client.get("/api/profile/stats").json()
        assert data["accuracyPercent"] == 100.0

    def test_trouble_peaks_require_two_or_more_wrong(self, auth_client, auth_user, peaks, db):
        add_guesses(db, auth_user.id, peaks[0].id, correct=0, wrong=1)  # below threshold
        add_guesses(db, auth_user.id, peaks[1].id, correct=0, wrong=2)  # at threshold

        data = auth_client.get("/api/profile/stats").json()
        trouble_ids = [p["peakId"] for p in data["troublePeaks"]]
        assert peaks[0].id not in trouble_ids
        assert peaks[1].id in trouble_ids

    def test_trouble_peaks_ordered_by_most_wrong(self, auth_client, auth_user, peaks, db):
        add_guesses(db, auth_user.id, peaks[0].id, correct=0, wrong=2)
        add_guesses(db, auth_user.id, peaks[1].id, correct=0, wrong=5)
        add_guesses(db, auth_user.id, peaks[2].id, correct=0, wrong=3)

        data = auth_client.get("/api/profile/stats").json()
        wrong_counts = [p["wrongCount"] for p in data["troublePeaks"]]
        assert wrong_counts == sorted(wrong_counts, reverse=True)

    def test_trouble_peaks_include_total_attempts(self, auth_client, auth_user, peaks, db):
        add_guesses(db, auth_user.id, peaks[0].id, correct=2, wrong=3)

        data = auth_client.get("/api/profile/stats").json()
        trouble = data["troublePeaks"][0]
        assert trouble["wrongCount"] == 3
        assert trouble["totalAttempts"] == 5

    def test_trouble_peaks_capped_at_five(self, auth_client, auth_user, peaks, db):
        for peak in peaks[:8]:
            add_guesses(db, auth_user.id, peak.id, correct=0, wrong=3)

        data = auth_client.get("/api/profile/stats").json()
        assert len(data["troublePeaks"]) <= 5

    def test_only_own_guesses_counted(self, auth_client, auth_user, peaks, db):
        from app.db.models import User
        other = User(id="other-user", username="Other", best_score=0)
        db.add(other)
        db.commit()
        add_guesses(db, "other-user", peaks[0].id, correct=10, wrong=0)
        add_guesses(db, auth_user.id, peaks[0].id, correct=1, wrong=0)

        data = auth_client.get("/api/profile/stats").json()
        assert data["totalGuesses"] == 1
        assert data["correctGuesses"] == 1
