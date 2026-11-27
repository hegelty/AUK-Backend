from datetime import datetime, timedelta
import logging
from threading import Lock
from time import monotonic
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup


COLUMN_URL = "https://news.naver.com/opinion/column"
LOOKBACK_DAYS = 3
RETRY_SECONDS = 300
logger = logging.getLogger(__name__)


class ColumnsUnavailable(Exception):
    pass


def fetch_columns(day):
    response = requests.get(COLUMN_URL, params={"date": day.strftime("%Y%m%d")}, timeout=(2, 3))
    response.raise_for_status()
    page = BeautifulSoup(response.content, "html.parser", from_encoding=response.encoding)
    articles = []
    for item in page.select(".opinion_calendar_content li"):
        anchor = item.select_one("a[href]")
        fields = [item.select_one(selector) for selector in ("strong", "p", ".sub_item")]
        if anchor is None or any(field is None for field in fields):
            continue
        title, description, author = (field.get_text(" ", strip=True) for field in fields)
        link = urljoin(COLUMN_URL, anchor["href"].strip())
        if not (title and description and author) or urlsplit(link).scheme not in ("https", "http"):
            continue
        articles.append(dict(title=title, description=description, author=author, link=link))
    return articles


class DailyColumns:
    def __init__(self):
        self.lock = Lock()
        self.day = None
        self.articles = []
        self.retry_at = 0

    def get(self, index):
        with self.lock:
            today = datetime.now(ZoneInfo("Asia/Seoul")).date()
            if self.day != today and monotonic() >= self.retry_at:
                self.refresh(today)
            if not self.articles:
                raise ColumnsUnavailable
            return self.articles[index]

    def refresh(self, today):
        fresh = []
        seen = set()
        try:
            for offset in range(LOOKBACK_DAYS):
                for article in fetch_columns(today - timedelta(days=offset)):
                    if article["link"] not in seen:
                        fresh.append(article)
                        seen.add(article["link"])
                if len(fresh) >= 2:
                    self.articles = fresh
                    # If today's feed was incomplete, check again later today.
                    self.day = today if offset == 0 else None
                    self.retry_at = 0 if offset == 0 else monotonic() + RETRY_SECONDS
                    return
        except requests.RequestException:
            logger.warning("Could not refresh the column feed", exc_info=True)
        # Keep both home cards available on transient failures. A cold cache
        # can still serve a single real article when that is all we found.
        if fresh and len(self.articles) < 2:
            self.articles = fresh
        self.retry_at = monotonic() + RETRY_SECONDS


columns = DailyColumns()


def get_column(id=0):
    return columns.get(id)
