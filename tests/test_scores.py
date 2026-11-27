from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app import app
from route.score import store_score


class ScoreTests(TestCase):
    def setUp(self):
        self.path = Path(self.enterContext(TemporaryDirectory())) / "score.db"
        self.enterContext(patch.dict(app.config, SCORE_DATABASE=self.path))
        self.client = app.test_client()

    def post(self, score, uid="local-install"):
        return self.client.post("/upload_score", data={"id": uid, "score": score})

    def rows(self, sql):
        with closing(sqlite3.connect(self.path)) as db:
            return list(db.execute(sql))

    def test_retry_updates_once_per_day_per_install(self):
        with patch("route.score.datetime") as clock:
            clock.now.return_value = datetime.fromisoformat("2026-11-27T23:59:00+09:00")
            self.assertEqual(self.post("0").get_data(as_text=True), "success")
            self.assertEqual(self.post("100").status_code, 200)
            self.post("31", uid="another-install")
            clock.now.return_value = datetime.fromisoformat("2026-11-28T00:00:00+09:00")
            self.post("80")
        self.assertEqual(self.rows("SELECT day, score FROM score ORDER BY day, score"),
                         [("2026-11-27", 31), ("2026-11-27", 100), ("2026-11-28", 80)])

    def test_migrates_latest_valid_score_and_preserves_originals(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TABLE score(id text, date text, score integer)")
            db.executemany("INSERT INTO score VALUES (?, ?, ?)", [
                ("old", "2023-11-30 12:00:00", 15), ("old", "2023-11-30 13:00:00", 25),
                ("old", "2023-12-01 23:00:00", 55), ("broken", "unknown", 999)])
        self.assertEqual(self.post("67").status_code, 200)
        self.assertEqual(self.post("67").status_code, 200)
        self.assertEqual(self.rows("SELECT score FROM score WHERE id='old' ORDER BY day"), [(25,), (55,)])
        self.assertEqual(self.rows("SELECT count(*) FROM score_legacy"), [(4,)])

    def test_concurrent_first_writes(self):
        with ThreadPoolExecutor(max_workers=3) as workers:
            list(workers.map(lambda score: store_score(self.path, "one-install", score), [5, 5, 5]))
        self.assertEqual(self.rows("SELECT score FROM score"), [(5,)])

    def test_rejects_invalid_input_before_creating_db(self):
        for value in ("", "101", "-1", "4.5", "abc"):
            self.assertEqual(self.post(value).status_code, 400)
        self.assertEqual(self.post("50", uid="   ").status_code, 400)
        self.assertFalse(self.path.exists())

    def test_storage_error_is_reported(self):
        with patch.dict(app.config, SCORE_DATABASE=self.path / "missing"), self.assertLogs(app.logger.name):
            response = self.post("42")
        self.assertEqual((response.status_code, response.get_data(as_text=True)), (503, "fail"))
