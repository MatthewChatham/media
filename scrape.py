import requests
import datetime as dt
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import os.path
import os
from argparse import ArgumentParser
from sqlalchemy import create_engine
import logging

PUBS = ['nyt', 'fox', 'wapo']
NOW = dt.datetime.now().strftime('%Y%m%dT%H%M')

parser = ArgumentParser()
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

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def fetch_foxnews():
    logger.info('Fetching headlines from FoxNews.com...')

    def _extract(element):
        logger.debug('Extracting headline title and url...')
        res = dict()
        title = element.find(attrs={'class': 'title'})
        if title is None:
            logger.debug('No element with class="title" found.')
            return {'headline': np.nan, 'url': np.nan}
        headline = title.text
        url = title.a['href']
        if '' in (headline.strip(), url.strip()):
            logger.debug('Empty headline or url.')
            return {'headline': np.nan, 'url': np.nan}
        res['headline'] = headline.strip()
        res['url'] = url.strip()
        logger.debug(f"Returning {res['headline']},{res['url']}")
        return res

    logger.info('Sending request to FoxNews.com...')
    soup = BeautifulSoup(requests.get('http://www.foxnews.com').text, 'lxml')
    logger.info('Finding articles...')
    headlines = soup.find_all(attrs={'class': 'article'})
    logger.info('Extracting headline titles and urls...')
    headlines_df = pd.DataFrame(list(map(_extract, headlines)))
    res = headlines_df.dropna().drop_duplicates()
    logger.info(f'Scraped {len(res)} headlines from Fox.')
    return res


def fetch_nytimes():
    logger.info('Fetching headlines from NYTimes.com...')

    def _extract(element):
        logger.debug(f'Extracting from {element}')
        res = dict()

        headline = element.text
        if headline is None:
            logger.debug('No title found')
            return {'headline': np.nan, 'url': np.nan}

        url = element.a
        if url is None:
            logger.debug('No url found')
            return {'headline': np.nan, 'url': np.nan}
        url = url['href']

        if '' in (headline.strip(), url.strip()):
            logger.debug('Empty title and/or url')
            return {'headline': np.nan, 'url': np.nan}

        res['headline'] = headline.strip()
        res['url'] = url
        logger.debug("Scraped {res['headline']},{res['url']}")
        return res

    logger.info('Sending request to NYTimes.com...')
    soup = BeautifulSoup(requests.get('https://www.nytimes.com').text, 'lxml')
    logger.info('Finding all story-headings...')
    elements = soup.find_all(attrs={'class': 'story-heading'})
    logger.info('Extracting titles and urls...')
    headlines_df = pd.DataFrame(list(map(_extract, elements)))
    res = headlines_df.dropna().drop_duplicates()
    logger.info(f"Scraped {len(res)} from NY Times.")
    return res


def fetch_wapo():
    logger.info('Fetching headlines from WashingtonPost.com...')

    def _extract(element):
        logger.debug(f'Extracting from {element}')
        res = dict()

        headline = element.text
        if headline is None:
            logger.debug('No title found')
            return {'headline': np.nan, 'url': np.nan}

        url = element['href']
        if url is None:
            logger.debug('No url found')
            return {'headline': np.nan, 'url': np.nan}

        if '' in (headline.strip(), url.strip()):
            logger.debug('Empty title and/or url')
            return {'headline': np.nan, 'url': np.nan}

        res['headline'] = headline.strip()
        res['url'] = url
        logger.debug("Scraped {res['headline']},{res['url']}")
        return res

    logger.info('Sending request to WashingtonPost.com...')
    url = 'https://www.washingtonpost.com'
    soup = BeautifulSoup(requests.get(url).text, 'lxml')
    logger.info('Finding all web_headlines...')
    elements = soup.find_all(attrs={'data-pb-field': 'web_headline'})
    logger.info('Extracting titles and urls...')
    headlines_df = pd.DataFrame(list(map(_extract, elements)))
    res = headlines_df.dropna().drop_duplicates()
    logger.info(f'Scraped {len(res)} from Washington Post.')
    return res


def main():
    # import pdb;pdb.set_trace()

    fetch_dict = {
        'nyt': fetch_nytimes,
        'fox': fetch_foxnews,
        'wapo': fetch_wapo}

    if args.pub == 'all':
        headlines = pd.DataFrame()
        logger.info(f'Fetching headlines from all publications...')
        for pub in PUBS:
            tmp = fetch_dict[pub]()
            tmp['pub'] = pub
            headlines = pd.concat([headlines, tmp])
    else:
        logger.info(f'Fetching headlines from {args.pub}...')
        headlines = fetch_dict[args.pub]()
        headlines['pub'] = args.pub

    # headlines['timestamp'] = NOW

    if args.file != 'heroku':
        logger.info(f'Saving {len(headlines)} to csv\
 {os.path.join(args.dir, args.file).format(NOW)}')
        headlines.to_csv(os.path.join(args.dir, args.file).format(NOW),
                         index=False, encoding='utf-8')
    else:
        db_url = os.environ['HEROKU_POSTGRESQL_CHARCOAL_URL']
        engine = create_engine(db_url)
        current = pd.read_sql_query('SELECT * FROM headlines;', engine)
        in_current = headlines['headline'].isin(current['headline'])
        toappend = headlines.loc[~in_current]
        if len(current) == 0:
            toappend = headlines
        toappend['timestamp'] = NOW
        logger.info(f'Loading {len(toappend)} to Heroku...')
        toappend.to_sql('headlines', engine, if_exists='append')


if __name__ == '__main__':
    main()
