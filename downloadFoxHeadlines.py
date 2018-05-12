from bs4 import BeautifulSoup
import requests
import pandas as pd
import datetime as dt
import numpy as np


def extractArticleFeatures(article):
    """Get title, URL, and whether article was spotlighted"""

    res = dict()

    # Get headline
    headline = article.find(attrs={'class': 'title'}).string
    res['headline'] = headline.strip() if headline is not None else np.nan

    # Get URL
    url = article.find(attrs={'class': 'title'}).a['href']
    res['url'] = url

    # Check if the article was spotlighted at the time
    classes = []
    p = article
    while p.name != '[document]':
        classes = classes + p.get('class', [None])
        p = p.parent
    spotlight = any(['spotlight' in cls for cls in classes if cls is not None])
    res['spotlight'] = spotlight

    return res


def main():

    url = 'http://www.foxnews.com/'
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'lxml')
    articles = soup.find_all(attrs={'class': 'article'})
    articles = pd.DataFrame(list(map(extractArticleFeatures, articles)))
    now = dt.datetime.now().strftime('%Y%m%dT%H%M')
    pth = 'C:\\Users\\Administrator\\Desktop\\media\\fox\\{}.csv'
    # articles = articles.drop_duplicates()
    articles.dropna().to_csv(pth.format(now), index=False, encoding='utf-8')


if __name__ == '__main__':

    main()
