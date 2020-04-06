import json
import requests
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


def get_corona(bot, update):
    text = update.message.text.split('/corona ')
    user = update.message.from_user.first_name
    if len(text) > 1:
        countries = text[1].split(',')
        countries = [i.lower().replace(' ', '') for i in countries]
        logger.info(f'{user} requested corona for {countries}')
        text = corona(countries)
    else:
        text = corona()
        logger.info(f'{user} requested corona')
    if text:
        bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=telegram.ParseMode.HTML)


def corona(countries=None):
    if countries is None:
        countries = ['italy', 'uk', 'france', 'spain', 'switzerland', 'usa', 'greece', 'brazil']
    countries.append('total:')
    url = 'https://www.worldometers.info/coronavirus/'
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as e:
        return e
    soup = BeautifulSoup(r.text, features='html.parser')
    table = soup.table
    table_rows = table.find_all('tr')
    rows = list()
    for tr in table_rows:
        td = tr.find_all('td')
        row = [i.text.strip(' ').replace(',', '').replace('+', '') for i in td[0:4]]
        if row and ((row[0].lower() in countries) or ('all' in countries)):
            row[1] = int(row[1])
            if not row[2]:
                row[2] = 0
            row[2] = int(row[2])
            if not row[3]:
                row[3] = 0
            row[3] = int(row[3])
            if row[0] == 'Switzerland':
                row[0] = 'Suisse'
            if row[0] == 'Total:':
                row[0] = 'Global'
            rows.append(human_format(r) if isinstance(r, int) and r > 10000 else r for r in row )
    fancy_table = tabulate.tabulate(rows, headers=['Pais', 'Cases', 'New', 'Deaths️'], tablefmt='simple', numalign='right')
    text = f'<pre>\n{fancy_table}\n</pre>'
    return text


def get_covid(bot, update):
    text = update.message.text.split('/covid ')
    user = update.message.from_user.first_name

    l = len(text)
    if l > 1:
        countries = text[1].split(',')
        if len(countries) > 1:
            countries = [i.lower().replace(' ', '') for i in countries]
            logger.info(f'{user} requested corona for {countries}')
            text = covid(countries)
        else:
            country = text[1]
            logger.info(f'{user} requested covid for {country}')
            text = detailed_covid(country)
    else:
        text = covid()
        logger.info(f'{user} requested covid')
    if text:
        bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=telegram.ParseMode.HTML)


def covid(countries=None):
    if countries is None:
        countries = ['italy', 'uk', 'france', 'spain', 'switzerland', 'usa', 'greece', 'brazil']
    try:
        res = requests.get(f'{covid_api}/countries').json()
    except (requests.exceptions.RequestException, json.decoder.JSONDecodeError) as e:
        return e
    rows = list()
    for i in res:
        if i['country'].lower() in countries:
            i['country'] = isoify(i['country'])
            if i['country'] == 'Switzerland':
                i['country'] = 'Suisse'
            for k in i.keys():
                if isinstance(i[k], int) and i[k] > 10000:
                    i[k] = human_format(i[k])
            row = [i.get('country'), i.get('cases'), i.get('todayCases'), i.get('deaths'), i.get('todayDeaths')]
            rows.append(row)
    table = tabulate.tabulate(rows, headers=['', 'Case', 'New', 'D️', 'ND'], tablefmt='simple', numalign='right', stralign='right')
    return f'<pre>\nCOVID-19 situation:\n{table}\n</pre>\nhttps://www.worldometers.info/coronavirus/#countries'


def detailed_covid(country):
    rows = list()
    try:
        res = requests.get(f'{covid_api}/countries/{country}').json()
    except (requests.exceptions.RequestException, json.decoder.JSONDecodeError) as e:
        return f'{e}'
    for k, v in res.items():
        if k == 'country':
            continue
        rows.append([k,v])
    table = tabulate.tabulate(rows, tablefmt='simple')
    return f'<pre>\nCOVID-19 situation in {country.capitalize()}\n{table}\n</pre>'


def get_covidbr(bot, update):
    user = update.message.from_user.first_name
    text = covid_br()
    logger.info(f'{user} requested covid BR')
    if text:
        bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=telegram.ParseMode.HTML)


def covid_br():
    headers = {'authority': 'xx9p7hp1p7.execute-api.us-east-1.amazonaws.com',
               'x-parse-application-id': 'unAFkcaNDeXajurGB7LChj8SgQYS2ptm'}
    rows = list()
    total_casos = 0
    total_mortes = 0
    try:
        res = requests.get('https://xx9p7hp1p7.execute-api.us-east-1.amazonaws.com/prod/PortalMapa', headers=headers).json()['results']
    except (requests.exceptions.RequestException, json.decoder.JSONDecodeError) as e:
        return e
    for i in res:
        row = [sigla(i.get('nome')), i.get('qtd_confirmado'), i.get('qtd_obito')]
        rows.append(row)
        total_casos += i.get('qtd_confirmado')
        total_mortes += i.get('qtd_obito')
    rows.append(['Total', total_casos, total_mortes])
    table = tabulate.tabulate(rows, headers=['Estado', 'Casos', 'Mortes'], tablefmt='psql')
    return f'<pre>\nBrasil sil sil:\n{table}\n</pre>\nhttps://covid.saude.gov.br'


