
import plotly.express as px
import pandas as pd
import json
import requests
import csv
import humanize


import config
import telegram
import logging
import tabulate

from utils import isoify, human_format, sigla
from bs4 import BeautifulSoup


cfg = config.cfg()
logger = logging.getLogger(__name__)
group_id = cfg.get('group_id')
my_chat_id = cfg.get('my_chat_id')
tabulate.MIN_PADDING = 0
covid_api = 'https://coronavirus-19-api.herokuapp.com'


def get_vaccine(update, context):
    text = update.message.text.split('/vac ')
    user = update.message.from_user.first_name
    table = vaccine()
    context.bot.send_message(chat_id=update.message.chat_id, text=table, parse_mode=telegram.ParseMode.HTML)
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open('vacina.png', 'rb'))


def vaccine():
    vac = 'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv'

    countries = ['Brazil', 'United Kingdom', 'Spain', 'Switzerland', 'France', 'Greece']
    df = pd.read_csv(vac, usecols=['location', 'date', 'total_vaccinations'])
    newdf = df[df.location.isin(countries)]
    # print(newdf)
    fig = px.line(
        newdf,
        x='date',
        y='total_vaccinations',
        color='location',
        title=f'Vaccination',
    )
    fig.add_layout_image()
    fig.write_image('vacina.png', width=1200, height=675)
    #
    # newdf.set_index('location', inplace=True)
    # newdf.last()
    table = pd.DataFrame()
    for i in countries:
        table = table.append(newdf.dropna()[newdf.location == i].tail(1), ignore_index=True)

    table['total_vaccinations'] = table['total_vaccinations'].astype(str)
    for i, row in table.iterrows():
        # print(i, row)
        # table.at[i, 'people_vaccinated'] = humanize.intword(table.at[i, 'people_vaccinated'])
        h = table.at[i, 'total_vaccinations'].rstrip('0').rstrip('.')
        # print(h.strip())

        # h = humanize.intword(int(table.at[i, 'people_vaccinated']))
        # print(h)
        # h = 0
        table.at[i, 'total_vaccinations'] = humanize.intword(h)

        # print(humanize.intword(table.columns.get_loc[i, 'people_vaccinated']))
    table.sort_values(by='location', inplace=True)
    # print(table.to_string(index=False))
    fancy_table = tabulate.tabulate(table, tablefmt='simple', numalign='right', showindex=False)
    # print(fancy_table)
    return f'<pre>\nCOVID-19 Vaccination:\n{fancy_table}</pre>'
