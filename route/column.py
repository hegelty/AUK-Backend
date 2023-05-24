import requests
from bs4 import BeautifulSoup as bs
import random


def get_column(id = None):
    url = "https://news.naver.com/opinion/column"
    response = requests.get(url)
    soup = bs(response.text, 'html.parser')
    items = soup.select('#ct > div > section.main_content > div > div.opinion_calendar_content._content_persist > ul > li')

    item = random.choice(items) if id is None else items[id]
    link = item.select_one('a')['href']
    title = item.select_one('strong').text
    description = item.select_one('p').text
    author = item.select_one('span.sub_item').text

    return {'link': link, 'title': title, 'description': description, 'author': author}
