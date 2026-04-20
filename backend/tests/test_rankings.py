from app.db.models import User


def seed_users(db, scores: dict[str, int]):
    for name, score in scores.items():
        db.add(User(id=name.lower(), username=name, best_score=score))
    db.commit()


class TestRankings:
    def test_empty_rankings(self, client, db):
        resp = client.get("/api/rankings")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_users_ordered_by_score_descending(self, client, db):
        seed_users(db, {"Alice": 500, "Bob": 200, "Charlie": 800})
        entries = client.get("/api/rankings").json()
        assert [e["username"] for e in entries] == ["Charlie", "Alice", "Bob"]

    def test_ranks_are_sequential(self, client, db):
        seed_users(db, {"Alice": 500, "Bob": 200, "Charlie": 800})
        entries = client.get("/api/rankings").json()
        assert [e["rank"] for e in entries] == [1, 2, 3]

    def test_zero_score_excluded(self, client, db):
        seed_users(db, {"Active": 400, "Inactive": 0})
        entries = client.get("/api/rankings").json()
        usernames = [e["username"] for e in entries]
        assert "Active" in usernames
        assert "Inactive" not in usernames

    def test_limit_parameter(self, client, db):
        for i in range(10):
            db.add(User(id=f"u{i}", username=f"User {i}", best_score=(i + 1) * 100))
        db.commit()
        entries = client.get("/api/rankings?limit=3").json()
        assert len(entries) == 3

    def test_guest_appears_after_finishing_with_nickname(self, client, peaks):
        session = client.post("/api/quiz/start").json()
        client.post("/api/quiz/finish", json={
            "sessionId": session["sessionId"],
            "score": 400,
            "nickname": "GuestHiker",
            "guestId": "guest-ranking-uuid",
        })
        entries = client.get("/api/rankings").json()
        assert any(e["username"] == "GuestHiker" for e in entries)

    def test_guest_rank_reflects_score_position(self, client, db, peaks):
        seed_users(db, {"TopUser": 1000})
        session = client.post("/api/quiz/start").json()
        resp = client.post("/api/quiz/finish", json={
            "sessionId": session["sessionId"],
            "score": 300,
            "nickname": "MidGuest",
            "guestId": "guest-mid-uuid",
        })
        assert resp.json()["rank"] == 2
