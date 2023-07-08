import datetime

import requests
from bs4 import BeautifulSoup as bs
import random

last_renewed_date = None
today_column = []


def get_column(id=None):
    date = datetime.datetime.now().strftime('%Y%m%d')
    print(id)
    global last_renewed_date
    if last_renewed_date != date:
        get_today_column(date)
    return today_column[id] if id is not None else today_column[0]



def get_today_column(date):
    global last_renewed_date
    global today_column

    url = "https://news.naver.com/opinion/column"
    response = requests.get(url, params={'date': date})
    soup = bs(response.text, 'html.parser')
    items = soup.select('#ct > div > section.main_content > div > div.opinion_calendar_content._content_persist > ul > li')
    if len(items) == 0:
        if date != last_renewed_date:
            get_today_column(str(int(date) - 1))
        return None

    for item in items:
        link = item.select_one('a')['href']
        title = item.select_one('strong').text
        description = item.select_one('p').text
        author = item.select_one('span.sub_item').text
        print(title)
        today_column.append({'link': link, 'title': title, 'description': description, 'author': author})

    last_renewed_date = date
    return True
