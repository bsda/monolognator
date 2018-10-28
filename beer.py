import os
import untappd
import requests
from operator import itemgetter
import logging
logger = logging.getLogger(__name__)


def get_untappd(search):
    logger.info(f'Searching untappd for {search}')
    client_id = os.getenv('untappd_client_id') 
    client_secret = os.getenv('untappd_client_secret')
    client = untappd.Untappd(client_id=client_id,
                             client_secret=client_secret,
                             redirect_url=None)

    re = client.search.beer(q=search)
    try:
        beer_id = re['response']['beers']['items'][0]['beer']['bid']
        result = client.beer.info(beer_id)

        untappd_beer = {'name': result['response']['beer']['beer_name'],
                    'label': result['response']['beer']['beer_label'],
                    'abv': round(result['response']['beer']['beer_abv'], 2),
                    'rating': round(result['response']['beer']['rating_score'], 2),
                    'style': result['response']['beer']['beer_style'],
                    'description': result['response']['beer']['beer_description'],
                    'count': result['response']['beer']['rating_count'],
                    'brewery': result['response']['beer']['brewery']['brewery_name']}
        return untappd_beer
    except IndexError:
        return {}


def get_ratebeer(search):
    logger.info(f'Searching Ratebeer for {search}')
    api_key = os.getenv('ratebeer_api_key')
    endpoint = 'https://api.ratebeer.com/v1/api/graphql'

    headers = {'content-type': 'application/json',
               'accept': 'application/json',
               'x-api-key': api_key}

    query = f'''
    {{
        beerSearch(query: "{search}") {{
            items {{
                id
                name
                brewer {{
                    name 
                }}
                description
                abv
                style {{
                    name
                }}
                styleScore
                averageRating
                ratingCount
                imageUrl
            }}
        }}
    }}
    '''
    re = requests.post(endpoint, headers=headers, json={'query': query})
    results = re.json()['data']['beerSearch']['items']
    sorted_results = sorted(results, key=itemgetter('ratingCount'), reverse=True)
    result = sorted_results[0]

    ratebeer_beer = {'name': result['name'],
                     'image': result['imageUrl'],
                     'abv': round(result['abv'], 2),
                     'rating': round(result['averageRating'], 2),
                     'count': result['ratingCount'],
                     'style': result['style']['name'],
                     'style_score': round(result['styleScore'], 2),
                     'description': result['description'],
                     'brewery': result['brewer']['name']}

    return ratebeer_beer


def beer(search):
    u_info = get_untappd(search)
    r_info = get_ratebeer(search)

    rating = {'u_name': u_info['name'],
              'u_abv': u_info['abv'],
              'u_style': u_info['style'],
              'u_brewery': u_info['brewery'],
              'u_rating': u_info['rating'],
              'u_count': u_info['count'],
              'r_name': r_info['name'],
              'r_abv': r_info['abv'],
              'r_style': r_info['style'],
              'r_brewery': r_info['brewery'],
              'r_rating': r_info['rating'],
              'r_count': r_info['count'],
              'r_style_score': r_info['style_score'],
              'image': r_info['image']}

    return rating
