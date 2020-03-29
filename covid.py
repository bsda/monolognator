import requests
import tabulate
import json


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
            if i['country'] == 'Switzerland':
                i['country'] = 'Suisse'
            row = [i.get('country'), i.get('cases'), i.get('todayCases'), i.get('deaths')]
            rows.append(row)
    table = tabulate.tabulate(rows, headers=['Pais', 'Case', 'New', '☠️'], tablefmt='psql', numalign='right')
    return f'<pre>\nCOVID-19 situation:\n{table}\n</pre>'

