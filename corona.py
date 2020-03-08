import requests
from datetime import datetime
import os
from bs4 import BeautifulSoup
import logging
import re
from tabulate import tabulate
logger = logging.getLogger(__name__)


def corona():
    uk = corona_uk(True)
    world = corona_world()
    text = f'{uk}\n\n{world}'
    return text


def corona_uk(ignore_last_update=False):
    logger.debug('Checking corona update')
    if not os.path.exists('/tmp/corona.txt'):
        with open('/tmp/corona.txt', 'w') as file:
            old = '2000-01-01T00:00:00.000Z'
            file.write(old)

    with open('/tmp/corona.txt', 'r') as file:
        last_update = file.read().splitlines()[0]
        last_update = datetime.strptime(last_update, '%Y-%m-%dT%H:%M:%S.%fZ')

    url = 'https://www.gov.uk/api/content/guidance/coronavirus-covid-19-information-for-the-public'
    res = requests.get(url).json()
    updated_at = res.get('updated_at')
    updated_at_obj = datetime.strptime(updated_at, '%Y-%m-%dT%H:%M:%S.%fZ')

    if updated_at_obj > last_update or ignore_last_update:
        logger.info('Sending Corona update')
        with open('/tmp/corona.txt', 'w') as file:
            file.write(str(updated_at))

        body = res.get('details').get('body')
        soup = BeautifulSoup(body.split('<h2')[1],  features='html.parser')
        table = soup.table
        table_rows = table.find_all('tr')
        rows = list()
        for tr in table_rows:
            td = tr.find_all('td')
            row = [i.text.replace(' and Yorkshire', '') for i in td]
            if row:
                rows.append(row)

        fancy_table = (tabulate(rows, headers=['Region', 'Cases'], tablefmt='simple'))


        text = soup.text.replace(' id="number-of-cases">', '')
        text = re.sub('(?m)Cases identified[^$]+', '', text)
        text = f'<b>UK Latest Update: {updated_at}</b>\n{text}\nCases by region:\n\n<pre>{fancy_table}</pre>'


        return text


def corona_world(countries=['Italy', 'UK', 'France', 'Spain', 'Switzerland', 'USA', 'Greece', 'Brazil']):
    countries.append('Total:')
    url = 'https://www.worldometers.info/coronavirus/'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, features='html.parser')
    table = soup.table
    table_rows = table.find_all('tr')
    rows = list()
    for tr in table_rows:
        td = tr.find_all('td')
        row = [i.text.replace(' ', '') for i in td[0:2] + td[3:4]]
        if row and row[0] in countries:
            if row[0] == 'Switzerland':
                row[0] = 'Swiss'
            if row[0] == 'Total:':
                row[0] = 'Global'
            cases = row[1].replace(',', '') or 0
            deaths = row[2].replace(',', '') or 0
            cfr = round(int(deaths) / int(cases) * 100, 2)
            cfr = f'{cfr}%'
            row.append(cfr)
            rows.append(row)
    fancy_table = (tabulate(rows, headers=['Country', 'Cases', '☠️', 'CFR'], tablefmt='simple'))

    text = 'Numbers for relevant countries:\n\n'
    text = text + f'<pre>{fancy_table}</pre>'
    return text

