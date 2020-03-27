import requests
import tabulate


base_url = 'https://coronavirus-19-api.herokuapp.com'


def covid(countries=['italy', 'uk', 'france', 'spain', 'switzerland', 'usa', 'greece', 'brazil']):
    # uk = corona_uk(True)
    world = summary(countries)
    text = f'{world}'
    return text

def total():
    res = requests.get(f'{base_url}/all').json()



def detailed(country):
    rows = list()
    try:
        res = requests.get(f'{base_url}/countries/{country}').json()
    except Exception as e:
        return '{e}'
    for k, v in res.items():
        if k == 'country':
            continue
        rows.append([k,v])
    table = tabulate.tabulate(rows, tablefmt='psql')
    return f'<pre>\nCOVID-19 situation in {country.capitalize()}\n{table}\n</pre>'


def summary(countries):
    res = requests.get(f'{base_url}/countries').json()
    rows = list()
    for i in res:
        if i['country'].lower() in countries:
            if i['country'] == 'Switzerland':
                i['country'] = 'Suisse'
            row = [i.get('country'), i.get('cases'), i.get('todayCases'), i.get('deaths')]
            rows.append(row)
    table = tabulate.tabulate(rows, headers=['Pais', 'Case', 'New', '☠️'], tablefmt='simple', numalign='right')
    return f'<pre>\nCOVID-19 situation:\n{table}\n</pre>'

