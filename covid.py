import requests
import tabulate
import json
from operator import itemgetter
from utils import isoify, human_format, sigla


base_url = 'https://coronavirus-19-api.herokuapp.com'


def covid(countries=['italy', 'uk', 'france', 'spain', 'switzerland', 'usa', 'greece', 'brazil']):
    # uk = corona_uk(True)
    world = summary(countries)
    return world

def total():
    res = requests.get(f'{base_url}/all').json()



def detailed(country):
    rows = list()
    try:
        res = requests.get(f'{base_url}/countries/{country}').json()
    except (requests.exceptions.RequestException, json.decoder.JSONDecodeError) as e:
        return f'{e}'
    for k, v in res.items():
        if k == 'country':
            continue
        rows.append([k,v])
    table = tabulate.tabulate(rows, tablefmt='simple')
    return f'<pre>\nCOVID-19 situation in {country.capitalize()}\n{table}\n</pre>'


def summary(countries):
    try:
        res = requests.get(f'{base_url}/countries').json()
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
            row = [i.get('country'), i.get('cases'), i.get('todayCases'), i.get('deaths'), i.get('todayDeaths'), i.get('critical')]
            rows.append(row)
    table = tabulate.tabulate(rows, headers=['', 'Case', 'New', 'D️', 'ND','Crit'], tablefmt='simple', numalign='right', stralign='right')
    return f'<pre>\nCOVID-19 situation:\n{table}\n</pre>\nhttps://www.worldometers.info/coronavirus/#countries'


def br():
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



