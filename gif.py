
import telegram
import random
import logging
import os
import requests
import uuid
logger = logging.getLogger(__name__)


# INLINE QUERY (GIF SEARCH)
def inlinequery(bot, update):
    """Handle the inline query."""
    query = update.inline_query.query
    logger.info(query)
    if not update.inline_query.offset:
        offset = 0
    else:
        offset = int(update.inline_query.offset)
    gifs = search_tenor(query, offset)
    results = list()
    for gif in gifs:
        results.append(telegram.InlineQueryResultGif(
            id=uuid.uuid4(),
            type='gif',
            gif_url=gif['url'],
            thumb_url=gif['thumb_url']
        ))
    update.inline_query.answer(results, timeout=5000, next_offset=int(offset)+40)


# GIPHY
def search_giphy(keyword, offset=0):
    gifs = []
    giphy_token = os.getenv('giphy_token')
    params = {'api_key': giphy_token, 'rating': 'r',
              'q': keyword, 'limit': 50, 'offset': offset}
    re = requests.get(f'https://api.giphy.com/v1/gifs/search', params=params)
    for g in re.json()['data']:
        gifs.append({'id': g['id'], 'url': g['images']['downsized_medium']['url'],
                     'thumb_url': g['images']['preview_gif']['url']})
    return gifs


def get_random_giphy(keyword=None):
    giphy_token=os.getenv('giphy_token')
    # offset = 0
    # gifs = list()
    params = {'api_key': giphy_token, 'rating': 'r'}
    if keyword:
        params.update({'tag': keyword})
    # for i in range(5):
    #     gifs.extend(search_tenor(keyword, offset=offset))
    #     offset+=40


    re = requests.get(f'https://api.giphy.com/v1/gifs/random', params=params)
    gif = re.json()['data']['images']['downsized_medium']['url']
    logger.info(f'Sending gif: {gif}')
    # gif = random.choice(gifs)['url']
    return gif


# TENOR
def search_tenor(keyword, offset=0):
    gifs = []
    tenor_token = os.getenv('tenor_token')
    params = {'key': tenor_token, 'media_filter': 'minimal',
              'q': keyword, 'limit': 40, 'pos': offset}
    re = requests.get(f'https://api.tenor.com/v1/search', params=params)
    for g in re.json()['results']:
        for m in g['media']:
            gifs.append({'id': g['id'], 'url': m['gif']['url'],
                         'thumb_url': m['gif']['preview']})
    return gifs


def get_random_tenor(keyword):
    tenor_token = os.getenv('tenor_token')
    params = {'key': tenor_token, 'media_filter': 'minimal',
              'q': keyword, 'limit': 50, 'pos': random.choice(range(300))}
    # print(params)
    re = requests.get(f'https://api.tenor.com/v1/random', params=params)
    gif = random.choice(re.json()['results'])['media'][0]['mediumgif']['url']
    logger.info(gif)
    return gif


def send_random_tenor(bot, update, keyword):
    gif = get_random_tenor(keyword)
    bot.send_document(chat_id=update.message.chat_id,
                      document=gif, timeout=100)









def informer(bot, update):
    # https://media1.tenor.com/images/9c58132c8e37a5d7f5a999332667967b/tenor.gif?itemid=13141855
    # https: // api.tenor.com / v1 / gifs? < parameters >
    tenor_token = os.getenv('tenor_token')
    params = {'key': tenor_token, 'ids': 13141855}
    # print(params)
    re = requests.get(f'https://api.tenor.com/v1/gifs', params=params)
    gif = re.json()['results'][0]['media'][0]['mediumgif']['url']
    logger.info(gif)
    bot.send_document(chat_id=update.message.chat_id, document=gif, timeout=1000)


def lula(bot, update):
    # https://media1.tenor.com/images/9c58132c8e37a5d7f5a999332667967b/tenor.gif?itemid=13141855
    # https: // api.tenor.com / v1 / gifs? < parameters >
    tenor_token = os.getenv('tenor_token')
    params = {'key': tenor_token, 'ids': 5544629}
    # print(params)
    re = requests.get(f'https://api.tenor.com/v1/gifs', params=params)
    gif = re.json()['results'][0]['media'][0]['mediumgif']['url']
    logger.info(gif)
    bot.send_document(chat_id=update.message.chat_id, document=gif, timeout=1000)