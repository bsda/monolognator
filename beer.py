import os
import untappd
import logging
import datetime
import pytz
logger = logging.getLogger(__name__)


def get_untappd_beer(bid, homebrew=False):
    keys = ['bid', 'beer_name', 'beer_label', 'beer_abv', 'rating_score',
            'beer_style', 'beer_description', 'rating_count']
    logger.info(f'Getting beer info for beer_id {bid}')
    client_id = os.getenv('untappd_client_id')
    client_secret = os.getenv('untappd_client_secret')
    client = untappd.Untappd(client_id=client_id,
                             client_secret=client_secret,
                             redirect_url=None)
    try:
        result = client.beer.info(bid)
        untappd_beer = {'bid': bid,
                        'name': result['response']['beer']['beer_name'],
                        'label': result['response']['beer']['beer_label_hd'],
                        'abv': round(result['response']['beer']['beer_abv'], 2),
                        'rating': round(result['response']['beer']['rating_score'], 2),
                        'style': result['response']['beer']['beer_style'],
                        'description': result['response']['beer']['beer_description'],
                        'count': result['response']['beer']['rating_count'],
                        'brewery': result['response']['beer']['brewery']['brewery_name'],
                        'country': result['response']['beer']['brewery']['country_name'],
                        'photos': list()}
        media = result['response']['beer']['media']['items']
        for m in media:
            untappd_beer['photos'].append(m['photo']['photo_img_md'])
        return untappd_beer
    except IndexError:
        return {}


def search_untappd(search, homebrew=False, limit=6):
    if homebrew:
        beertype = 'homebrew'
    else:
        beertype = 'beers'
    beers = list()
    keys = ['bid', 'beer_name', 'beer_label', 'beer_abv', 'rating_score',
            'beer_style', 'beer_description', 'rating_count']
    logger.info(f'Searching untappd for {search}')
    client_id = os.getenv('untappd_client_id')
    client_secret = os.getenv('untappd_client_secret')
    client = untappd.Untappd(client_id=client_id,
                             client_secret=client_secret,
                             redirect_url=None)

    re = client.search.beer(q=search, limit=limit)['response'][beertype]['items']
    for beer in re:
        beers.append({'bid': beer['beer']['bid'],
                      'name': beer['beer']['beer_name'],
                      'checkin_count': beer['checkin_count'],
                      'brewery': beer['brewery']['brewery_name'],
                      'country': beer['brewery']['country_name']})
    return beers


def get_recent_check_ins(user):
    logger.info(f'Getting {user} check-ins')
    client_id = os.getenv('untappd_client_id')
    client_secret = os.getenv('untappd_client_secret')
    client = untappd.Untappd(client_id=client_id,
                             client_secret=client_secret,
                             redirect_url=None)

    re = client.user.checkins(user, limit=50)
    check_ins = re.get('response').get('checkins').get('items')
    recent_check_ins = {'user': user, 'checkins': []}
    for c in check_ins:
        date = datetime.datetime.strptime(c['created_at'], '%a, %d %b %Y %H:%M:%S %z')
        recent_check_ins['checkins'].append({
            'date': date,
            'beer': c.get('beer').get('beer_name'),
            'brewery': c.get('brewery').get('brewery_name'),
            'rating': c.get('rating_score')
        })
    return recent_check_ins


def new_latest_checkin(user):
    c = get_recent_check_ins(user)
    latest = c.get('checkins')[0]
    today = datetime.datetime.today().replace(tzinfo=pytz.utc)
    days = (today - latest.get('date')).days
    latest_check_in = {
        'user': user,
        'days': days,
        'beer': latest.get('beer'),
        'brewery': latest.get('brewery')
    }
    return latest_check_in


def count_week_checkins(checkins):
    count = 0
    seven_days = datetime.datetime.now().replace(tzinfo=pytz.utc) - datetime.timedelta(days=7)
    for i in checkins:
        if i['date'] > seven_days:
            count +=1
    return count


def get_wet_scores(users):
    scores = list()
    for user in users:
        checkins = get_recent_check_ins(user)['checkins']
        wet_score = count_week_checkins(checkins)
        scores.append({'user': user, 'score': wet_score})
    return scores


def get_dry_scores(users):
    scores = list()
    for u in users:
        scores.append(new_latest_checkin(u))
    return scores

