# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import os
import psycopg2
import pandas as pd

# Get data
DATABASE_URL = os.environ['HEROKU_POSTGRESQL_CHARCOAL_URL']
PASSWORD = os.environ['PGPASSWORD']
QUERY = 'SELECT index, headline AS text, pub, url FROM headlines;'
conn = psycopg2.connect(DATABASE_URL, sslmode='require', password=PASSWORD)
headlines = pd.read_sql_query(QUERY, conn, index_col='index')
corpus = headlines[['text', 'pub']]
corpus['pub'] = corpus['pub'].str.strip()
corpus.drop_duplicates(inplace=True)

count_by_pub = corpus.pub.value_counts()

# Define app
app = dash.Dash()
server = app.server
app.layout = html.Div(children=[

    dcc.Graph(
        id='count-by-pub',
        figure={
            'data': [
                {'x': count_by_pub.index,
                 'y': count_by_pub,
                 'type': 'bar',
                 'name': 'Count'
                }
            ],
            'layout': {
                'title': 'Count of headlines by publication'
            }
        }
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)