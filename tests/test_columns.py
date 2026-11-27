from datetime import date, datetime
from unittest import TestCase
from unittest.mock import Mock, patch

import requests

from app import app
from route import column


def article(title):
    return dict(title=title, description="본문", author="필자", link="https://example.org/" + title)


class ColumnTests(TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.cache = column.DailyColumns()
        self.enterContext(patch.object(column, "columns", self.cache))
        self.clock = self.enterContext(patch.object(column, "datetime"))
        self.clock.now.return_value = datetime(2026, 1, 1)

    @patch.object(column, "fetch_columns")
    def test_new_day_replaces_both_cards(self, fetch):
        fetch.side_effect = [[article("one"), article("two")], [article("three"), article("four")]]
        self.assertEqual(self.client.get("/column?id=1").json, article("two"))
        self.clock.now.return_value = datetime(2026, 1, 2)
        self.assertEqual(self.client.get("/column?id=0").json, article("three"))
        self.assertEqual(self.client.get("/column?id=1").json, article("four"))
        self.assertEqual(fetch.call_count, 2)

    @patch.object(column, "fetch_columns")
    def test_calendar_fallback_and_retry(self, fetch):
        fetch.side_effect = [[], [article("prev1"), article("prev2")], [article("new1"), article("new2")]]
        with patch.object(column, "monotonic", return_value=1):
            self.assertEqual(self.client.get("/column").json, article("prev1"))
            self.assertEqual(self.client.get("/column?id=1").json, article("prev2"))
        self.assertEqual([c.args[0] for c in fetch.call_args_list], [date(2026, 1, 1), date(2025, 12, 31)])
        with patch.object(column, "monotonic", return_value=column.RETRY_SECONDS + 2):
            self.assertEqual(self.client.get("/column").json, article("new1"))

    @patch.object(column, "fetch_columns")
    def test_unavailable_feed_and_bad_index(self, fetch):
        fetch.return_value = []
        self.assertEqual(self.client.get("/column?id=unknown").status_code, 400)
        self.assertEqual(self.client.get("/column").status_code, 503)
        self.assertEqual(self.client.get("/column").status_code, 503)
        self.assertEqual(fetch.call_count, column.LOOKBACK_DAYS)

    @patch.object(column, "fetch_columns")
    def test_upstream_failure_keeps_last_good_feed(self, fetch):
        fetch.side_effect = [[article("a"), article("b")], requests.Timeout()]
        self.assertEqual(self.client.get("/column?id=2").status_code, 404)
        self.clock.now.return_value = datetime(2026, 1, 2)
        with self.assertLogs(column.logger.name):
            self.assertEqual(self.client.get("/column?id=1").json, article("b"))

    @patch.object(column.requests, "get")
    def test_extracts_android_fields_and_skips_incomplete_items(self, get):
        html = '<div class="opinion_calendar_content"><ul><li></li><li><a href="/a"><strong>제목</strong></a><p>본문</p><span class="sub_item">필자</span></li></ul></div>'
        bad_link = '<li><a href="https://[broken"><strong>제목</strong></a><p>본문</p><span class="sub_item">필자</span></li>'
        html = html.replace("<li></li>", "<li></li>" + bad_link)
        get.return_value = Mock(content=html.encode(), encoding="utf-8")
        self.assertEqual(column.fetch_columns(date(2026, 1, 1)), [
            dict(title="제목", description="본문", author="필자", link="https://news.naver.com/a")])
        self.assertEqual(get.call_args.kwargs["params"], {"date": "20260101"})
        self.assertTrue(get.call_args.kwargs["timeout"])
