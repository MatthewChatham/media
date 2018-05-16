import requests
import datetime as dt
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import os.path
import os
from argparse import ArgumentParser

PUBS = ['nyt', 'fox', 'wapo']
NOW = dt.datetime.now().strftime('%Y%m%dT%H%M')

parser = ArgumentParser()
# TODO: arguments
parser.add_argument(
    '-p', '--pub',
    default='all',
    help='Publication to scrape (fox|nyt|wapo).')
parser.add_argument(
    '-d', '--dir',
    default=os.getcwd(),
    help='Output directory (default wd).')
parser.add_argument(
    '-f', '--file',
    default='all{}.csv'.format(NOW),
    help='Output file (default allYYYMMDDTHHMM.csv')
args = parser.parse_args()
if args.pub != 'all' and args.file == 'all{}.csv'.format(NOW):
    args.file = args.pub + '{}.csv'
    print(args.file)


def fetch_foxnews():
    def _extract(element):
        res = dict()
        title = element.find(attrs={'class': 'title'})
        if title is None:
            return {'headline': np.nan, 'url': np.nan}
        headline = title.text
        url = title.a['href']
        if '' in (headline.strip(), url.strip()):
            return {'headline': np.nan, 'url': np.nan}
        res['headline'] = headline.strip()
        res['url'] = url.strip()
        return res

    soup = BeautifulSoup(requests.get('http://www.foxnews.com').text, 'lxml')
    headlines = soup.find_all(attrs={'class': 'article'})
    headlines_df = pd.DataFrame(list(map(_extract, headlines)))
    return headlines_df.dropna().drop_duplicates()


def fetch_nytimes():
    def _extract(element):
        res = dict()

        headline = element.text
        if headline is None:
            return {'headline': np.nan, 'url': np.nan}

        url = element.a
        if url is None:
            return {'headline': np.nan, 'url': np.nan}
        url = url['href']

        if '' in (headline.strip(), url.strip()):
            return {'headline': np.nan, 'url': np.nan}

        res['headline'] = headline.strip()
        res['url'] = url
        return res

    soup = BeautifulSoup(requests.get('https://www.nytimes.com').text, 'lxml')
    elements = soup.find_all(attrs={'class': 'story-heading'})
    headlines_df = pd.DataFrame(list(map(_extract, elements)))
    return headlines_df.dropna().drop_duplicates()


def fetch_wapo():
    def _extract(element):
        res = dict()

        headline = element.text
        if headline is None:
            return {'headline': np.nan, 'url': np.nan}

        url = element['href']
        if url is None:
            return {'headline': np.nan, 'url': np.nan}

        if '' in (headline.strip(), url.strip()):
            return {'headline': np.nan, 'url': np.nan}

        res['headline'] = headline.strip()
        res['url'] = url
        return res

    url = 'https://www.washingtonpost.com'
    soup = BeautifulSoup(requests.get(url).text, 'lxml')
    elements = soup.find_all(attrs={'data-pb-field': 'web_headline'})
    headlines_df = pd.DataFrame(list(map(_extract, elements)))
    return headlines_df.dropna().drop_duplicates()


def main():

    # import pdb;pdb.set_trace()

    fetch_dict = {
        'nyt': fetch_nytimes,
        'fox': fetch_foxnews,
        'wapo': fetch_wapo}

    if args.pub == 'all':
        headlines = pd.DataFrame()
        for pub in PUBS:
            tmp = fetch_dict[pub]()
            tmp['pub'] = pub
            headlines = pd.concat([headlines, tmp])
    else:
        headlines = fetch_dict[args.pub]()
        headlines['pub'] = args.pub

    headlines['timestamp'] = NOW

    headlines.to_csv(os.path.join(args.dir, args.file).format(NOW),
                     index=False, encoding='utf-8')


if __name__ == '__main__':
    main()
