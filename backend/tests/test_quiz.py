from app.db.models import Guess, User


def start(client, peaks):
    resp = client.post("/api/quiz/start")
    assert resp.status_code == 200
    return resp.json()


class TestStartQuiz:
    def test_returns_session_and_questions(self, client, peaks):
        data = start(client, peaks)
        assert "sessionId" in data
        assert len(data["questions"]) == 10

    def test_each_question_has_four_options(self, client, peaks):
        data = start(client, peaks)
        for q in data["questions"]:
            assert len(q["options"]) == 4

    def test_correct_answer_is_among_options(self, client, peaks):
        data = start(client, peaks)
        for q in data["questions"]:
            assert q["peak"]["name"] in q["options"]

    def test_requires_at_least_four_peaks(self, client, db):
        # Only 3 peaks — not enough
        for i in range(3):
            from app.db.models import Peak, Picture
            p = Peak(name=f"Tiny Peak {i}", elevation=1000)
            db.add(p)
            db.flush()
            db.add(Picture(peak_id=p.id, cdn_url=f"https://cdn.example.com/{i}",
                           original_url=f"http://example.com/{i}.jpg"))
        db.commit()
        resp = client.post("/api/quiz/start")
        assert resp.status_code == 503


class TestAnswer:
    def test_correct_answer_awards_points(self, client, peaks):
        session = start(client, peaks)
        q = session["questions"][0]
        resp = client.post("/api/quiz/answer", json={
            "sessionId": session["sessionId"],
            "questionId": q["id"],
            "answer": q["peak"]["name"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["correct"] is True
        assert data["pointsEarned"] == 100
        assert data["totalPoints"] == 100

    def test_wrong_answer_awards_no_points(self, client, peaks):
        session = start(client, peaks)
        q = session["questions"][0]
        wrong = next(opt for opt in q["options"] if opt != q["peak"]["name"])
        resp = client.post("/api/quiz/answer", json={
            "sessionId": session["sessionId"],
            "questionId": q["id"],
            "answer": wrong,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["correct"] is False
        assert data["pointsEarned"] == 0
        assert data["totalPoints"] == 0

    def test_score_accumulates_across_answers(self, client, peaks):
        session = start(client, peaks)
        sid = session["sessionId"]
        for q in session["questions"][:3]:
            client.post("/api/quiz/answer", json={
                "sessionId": sid,
                "questionId": q["id"],
                "answer": q["peak"]["name"],
            })
        resp = client.post("/api/quiz/answer", json={
            "sessionId": sid,
            "questionId": session["questions"][3]["id"],
            "answer": session["questions"][3]["peak"]["name"],
        })
        # streak kicks in at 3rd correct: 100 + 100 + 200 + 300 = 700
        assert resp.json()["totalPoints"] == 700

    def test_duplicate_answer_does_not_corrupt_session(self, client, peaks):
        """A 409 on a duplicate submission must leave the session intact for future questions."""
        session = start(client, peaks)
        sid = session["sessionId"]
        q0 = session["questions"][0]
        q1 = session["questions"][1]

        first = client.post("/api/quiz/answer", json={
            "sessionId": sid,
            "questionId": q0["id"],
            "answer": q0["peak"]["name"],
        }).json()
        assert first["totalPoints"] == 100

        dup = client.post("/api/quiz/answer", json={
            "sessionId": sid,
            "questionId": q0["id"],
            "answer": q0["peak"]["name"],
        })
        assert dup.status_code == 409

        second = client.post("/api/quiz/answer", json={
            "sessionId": sid,
            "questionId": q1["id"],
            "answer": q1["peak"]["name"],
        }).json()
        assert second["correct"] is True
        assert second["totalPoints"] == 200

    def test_duplicate_answer_rejected(self, client, peaks):
        """Answering the same question twice must not award points twice."""
        session = start(client, peaks)
        q = session["questions"][0]
        payload = {
            "sessionId": session["sessionId"],
            "questionId": q["id"],
            "answer": q["peak"]["name"],
        }
        first = client.post("/api/quiz/answer", json=payload).json()
        assert first["correct"] is True
        assert first["totalPoints"] == 100

        second = client.post("/api/quiz/answer", json=payload)
        assert second.status_code == 409

    def test_unknown_session_returns_404(self, client, peaks):
        resp = client.post("/api/quiz/answer", json={
            "sessionId": "nonexistent",
            "questionId": 1,
            "answer": "Anything",
        })
        assert resp.status_code == 404

    def test_no_db_write_at_answer_time(self, auth_client, auth_user, peaks, db):
        """Guesses must not be written to DB during /answer — only at /finish."""
        session = start(auth_client, peaks)
        q = session["questions"][0]
        auth_client.post("/api/quiz/answer", json={
            "sessionId": session["sessionId"],
            "questionId": q["id"],
            "answer": q["peak"]["name"],
        })
        assert db.query(Guess).filter(Guess.user_id == auth_user.id).count() == 0

    def test_guess_saved_for_authenticated_user_at_finish(self, auth_client, auth_user, peaks, db):
        session = start(auth_client, peaks)
        sid = session["sessionId"]
        q = session["questions"][0]
        auth_client.post("/api/quiz/answer", json={
            "sessionId": sid,
            "questionId": q["id"],
            "answer": q["peak"]["name"],
        })
        auth_client.post("/api/quiz/finish", json={"sessionId": sid, "score": 100})
        guesses = db.query(Guess).filter(Guess.user_id == auth_user.id).all()
        assert len(guesses) == 1
        assert guesses[0].is_correct is True

    def test_guess_not_saved_for_anonymous_user(self, client, peaks, db):
        session = start(client, peaks)
        q = session["questions"][0]
        client.post("/api/quiz/answer", json={
            "sessionId": session["sessionId"],
            "questionId": q["id"],
            "answer": q["peak"]["name"],
        })
        assert db.query(Guess).count() == 0


class TestNextQuestion:
    def test_returns_unseen_peak(self, client, peaks):
        session = start(client, peaks)
        sid = session["sessionId"]
        seen_ids = {q["id"] for q in session["questions"]}

        resp = client.get(f"/api/quiz/next/{sid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] not in seen_ids

    def test_unknown_session_returns_404(self, client):
        resp = client.get("/api/quiz/next/nonexistent")
        assert resp.status_code == 404

    def test_next_question_never_returns_already_answered_peak(self, client, db):
        """next_question must not return a peak the user already answered.

        Setup: 4 peaks where peak-0 has two CDN pictures. The initial batch
        uses all 4 peaks (picture-A of peak-0). After answering all 4, only
        picture-B of peak-0 is unseen — without the fix next_question returns
        peak-0 again, and answering it causes a 409.
        """
        from app.db.models import Peak, Picture

        peak0 = Peak(name="Multi Pic Peak", elevation=4000)
        db.add(peak0)
        db.flush()
        db.add(Picture(peak_id=peak0.id, cdn_url="https://cdn.example.com/p0a",
                       original_url="http://example.com/p0a.jpg"))
        db.add(Picture(peak_id=peak0.id, cdn_url="https://cdn.example.com/p0b",
                       original_url="http://example.com/p0b.jpg"))
        for i in range(1, 4):
            p = Peak(name=f"Single Pic Peak {i}", elevation=3000 + i * 100)
            db.add(p)
            db.flush()
            db.add(Picture(peak_id=p.id, cdn_url=f"https://cdn.example.com/p{i}",
                           original_url=f"http://example.com/p{i}.jpg"))
        db.commit()

        session = start(client, db)
        sid = session["sessionId"]

        for q in session["questions"]:
            client.post("/api/quiz/answer", json={
                "sessionId": sid,
                "questionId": q["id"],
                "answer": q["peak"]["name"],
            })

        # Only peak-0's second picture is unseen — next must not return it
        resp = client.get(f"/api/quiz/next/{sid}")
        if resp.status_code == 200:
            assert resp.json()["id"] != peak0.id, \
                "next_question returned an already-answered peak"

    def test_exhausted_peaks_returns_404(self, client, db):
        # Only 4 peaks — all go into the initial batch
        from app.db.models import Peak, Picture
        for i in range(4):
            p = Peak(name=f"Small Peak {i}", elevation=1000)
            db.add(p)
            db.flush()
            db.add(Picture(peak_id=p.id, cdn_url=f"https://cdn.example.com/s{i}",
                           original_url=f"http://example.com/s{i}.jpg"))
        db.commit()

        session = start(client, db)
        resp = client.get(f"/api/quiz/next/{session['sessionId']}")
        assert resp.status_code == 404


class TestFinishQuiz:
    def test_guest_score_saved_with_nickname(self, client, peaks, db):
        session = start(client, peaks)
        resp = client.post("/api/quiz/finish", json={
            "sessionId": session["sessionId"],
            "score": 300,
            "nickname": "GuestPlayer",
            "guestId": "guest-test-uuid",
        })
        assert resp.status_code == 200
        assert "rank" in resp.json()

        guest = db.get(User, "guest-test-uuid")
        assert guest is not None
        assert guest.username == "GuestPlayer"
        assert guest.best_score == 300

    def test_guest_score_not_saved_without_nickname(self, client, peaks, db):
        session = start(client, peaks)
        client.post("/api/quiz/finish", json={
            "sessionId": session["sessionId"],
            "score": 300,
        })
        assert db.query(User).count() == 0

    def test_authenticated_user_best_score_updated(self, auth_client, auth_user, peaks, db):
        session = start(auth_client, peaks)
        auth_client.post("/api/quiz/finish", json={
            "sessionId": session["sessionId"],
            "score": 500,
        })
        db.refresh(auth_user)
        assert auth_user.best_score == 500

    def test_best_score_not_overwritten_by_lower_score(self, auth_client, auth_user, peaks, db):
        auth_user.best_score = 800
        db.commit()

        session = start(auth_client, peaks)
        auth_client.post("/api/quiz/finish", json={
            "sessionId": session["sessionId"],
            "score": 200,
        })
        db.refresh(auth_user)
        assert auth_user.best_score == 800

    def test_session_removed_after_finish(self, client, peaks):
        from app.api.routes.quiz import _sessions
        session = start(client, peaks)
        sid = session["sessionId"]
        assert sid in _sessions

        client.post("/api/quiz/finish", json={"sessionId": sid, "score": 0})
        assert sid not in _sessions
