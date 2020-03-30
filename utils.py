import flag
import pycountry


def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


def emojify(country):
    if country == 'England':
        return '🏴󠁧󠁢󠁥󠁮󠁧󠁿󠁧󠁢󠁳󠁣󠁴󠁿'
    if country == 'Scotland':
        return '🏴󠁧󠁢󠁳󠁣󠁴󠁿'
    if country == 'Russia':
        country = 'Russian Federation'
    try:
        alpha_2 = pycountry.countries.get(name=country).alpha_2
        emoji = flag.flagize(f':{alpha_2}:')
    except Exception:
        return '🏴‍☠️'
    return emoji


def isoify(country):
    try:
        alpha_2 = pycountry.countries.get(name=country).alpha_2
    except Exception:
        return country
    return alpha_2


def human_format(num):
    num = float('{:.2g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

def sigla(estado):
    siglas = {
        "Acre": "AC",
        "Alagoas": "AL",
        "Amapá": "AP",
        "Amazonas": "AM",
        "Bahia": "BA",
        "Ceará": "CE",
        "Distrito Federal": "DF",
        "Espírito Santo": "ES",
        "Goiás": "GO",
        "Maranhão": "MA",
        "Mato Grosso": "MT",
        "Mato Grosso do Sul": "MS",
        "Minas Gerais": "MG",
        "Pará": "PA",
        "Paraíba": "PB",
        "Paraná": "PR",
        "Pernambuco": "PE",
        "Piauí": "PI",
        "Rio de Janeiro": "RJ",
        "Rio Grande do Norte": "RN",
        "Rio Grande do Sul": "RS",
        "Rondônia": "RO",
        "Roraima": "RR",
        "Santa Catarina": "SC",
        "São Paulo": "SP",
        "Sergipe": "SE",
        "Tocantins": "TO"
    }
    return siglas[estado]
