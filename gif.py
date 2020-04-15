import re
import telegram
import random
import logging
import yaml
import requests
import uuid
import config
from updater import get_updater
from google.cloud import firestore
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import Filters, InlineQueryHandler, RegexHandler
from telegram.ext import CallbackQueryHandler


logger = logging.getLogger(__name__)
cfg = config.cfg()


# with open('gifs.yml') as f:
#     gifs = yaml.load(f, Loader=yaml.FullLoader)

# def get_updater():
#     token = cfg.get('telegram_token')
#     updater = Updater(token, request_kwargs={'read_timeout': 6, 'connect_timeout': 7})
#     return updater

def get_gif_filters():
    db = firestore.Client.from_service_account_json(json_credentials_path='./sa.json', project='peppy-house-263912')
    doc_ref = db.collection('gifs').document('filters')
    # doc_ref.set(gifs)
    doc = doc_ref.get()
    return doc.to_dict()


gif_filters = get_gif_filters()


def list_aliases(keyword):
    key = get_gif_key(keyword)
    aliases = gif_filters[key].get('aliases')
    return ', '.join(aliases)


def get_aliases(bot, update):
    word = update.message.text.split('/list_alias ')[1]
    aliases = list_aliases(word).replace("*", "\\*")
    text = f'Aliases for *{word}*: {aliases}'
    bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)


def update_aliases(keyword, alias):
    db = firestore.Client.from_service_account_json(json_credentials_path='./sa.json', project='peppy-house-263912')
    doc_ref = db.collection('gifs').document('filters')
    key = get_gif_key(keyword)
    gif_filters[key]['aliases'].append(alias)
    gif_filters[key]['aliases'] = list(set(gif_filters[key]['aliases']))
    doc_ref.set(gif_filters)
    filters = get_gif_filters()
    aliases = filters[key].get('aliases')
    updater = get_updater()
    print(word_watcher_regex())
    updater.dispatcher.remove_handler(RegexHandler)
    updater.dispatcher.add_handler(RegexHandler(word_watcher_regex(), word_watcher_gif))
    return aliases


def add_alias(bot, update):
    command = update.message.text.split('/add_alias ')[1]
    keyword, alias = command.split('=')
    aliases = ', '.join(update_aliases(keyword, alias)).replace("*", "\\*")
    text = f'Filter updated, *{alias}* added to {keyword}\n'
    text += f'*New filter*:\n{aliases}'
    bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)



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


def search_giphy(keyword, offset=0):
    gifs = []
    giphy_token = cfg.get('giphy_token')
    params = {'api_key': giphy_token, 'rating': 'r',
              'q': keyword, 'limit': 50, 'offset': offset}
    res = requests.get(f'https://api.giphy.com/v1/gifs/search', params=params)
    for g in res.json()['data']:
        gifs.append({'id': g['id'], 'url': g['images']['downsized_medium']['url'],
                     'thumb_url': g['images']['preview_gif']['url']})
    return gifs


def get_random_giphy(keyword=None):
    giphy_token=cfg.get('giphy_token')
    params = {'api_key': giphy_token, 'rating': 'r'}
    if keyword:
        params.update({'tag': keyword})
    res = requests.get(f'https://api.giphy.com/v1/gifs/random', params=params)
    gif = res.json()['data']['images']['downsized_medium']['url']
    logger.info(f'Sending gif: {gif}')
    return gif


def search_tenor(keyword, offset=0):
    gifs = []
    tenor_token = cfg.get('tenor_token')
    params = {'key': tenor_token, 'media_filter': 'minimal',
              'q': keyword, 'limit': 40, 'pos': offset}
    res = requests.get(f'https://api.tenor.com/v1/search', params=params)
    for g in res.json()['results']:
        for m in g['media']:
            gifs.append({'id': g['id'], 'url': m['gif']['url'],
                         'thumb_url': m['gif']['preview']})
    return gifs


def get_random_tenor(keyword):
    tenor_token = cfg.get('tenor_token')
    params = {'key': tenor_token, 'media_filter': 'minimal',
              'q': keyword, 'limit': 50, 'pos': random.choice(range(50))}
    try:
        res = requests.get(f'https://api.tenor.com/v1/random', params=params).json()['results']
        gifs = [ i for i in res if i['media'][0]['mediumgif']['size'] <= 10000000]
        gif = random.choice(gifs)['media'][0]['mediumgif']['url']
        logger.info(gif)
        return gif
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to get tenor gif for {keyword}: {e}')
        return e


def send_random_tenor(bot, update, keyword):
    gif = get_random_tenor(keyword)
    bot.send_document(chat_id=update.message.chat_id,
                         document=gif, timeout=5000)


def send_tenor(bot, update, gifid):
    gif = get_tenor_gif(gifid)
    logger.info(f'Sending gif: {gif}')
    bot.send_document(chat_id=update.message.chat_id,
                         document=gif, timeout=5000)


def get_tenor_gif(gifid):
    tenor_token = cfg.get('tenor_token')
    params = {'key': tenor_token, 'ids': gifid}
    res = requests.get(f'https://api.tenor.com/v1/gifs', params=params)
    try:
        gif = res.json()['results'][0]['media'][0]['mediumgif']['url']
        return gif
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to get {gifid} on tenor: {e}')


def word_watcher_regex():
    gif_filters = get_gif_filters()
    keys = ([i for i in gif_filters.keys()])
    alias_lists = [gif_filters[i].get('aliases') for i in gif_filters.keys() if gif_filters[i].get('aliases')]
    aliases = ([i for sublist in alias_lists for i in sublist])
    regex = re.compile('|'.join(keys + aliases), re.IGNORECASE)
    return regex


def get_gif_key(word):
    gif_filters = get_gif_filters()
    logger.info(f'Getting gif key for {word}')
    for i in gif_filters.keys():
        if gif_filters[i].get('aliases'):
            aliasrex = re.compile('|'.join(gif_filters[i].get('aliases')), re.IGNORECASE)
            if word in gif_filters[i].get('aliases') or re.search(aliasrex, word):
                return i


def word_watcher_gif(bot, update):
    gif_filters = get_gif_filters()
    regex = word_watcher_regex()
    msg = update.message.text.lower()
    logger.info(f'Start word watcher with {msg}')
    for m in regex.findall(msg):
        # check if word is key
        if m in gif_filters:
            if gif_filters.get(m).get('type') == 'random':
                keyword = random.choice(gif_filters.get(m).get('keywords'))
                logger.info(f'Word Watcher: {keyword}')
                send_random_tenor(bot, update, keyword)
            else:
                logger.info(f'Word Watcher: {m}')
                gifid = random.choice(gif_filters.get(m).get('tenor_gif'))
                send_tenor(bot, update, gifid)
        else:
            key = get_gif_key(m)
            if gif_filters[key]['type'] == 'static':
                gifid = random.choice(gif_filters.get(key).get('tenor_gif'))
                send_tenor(bot, update, gifid)
            else:
                keyword = random.choice(gif_filters.get(key).get('keywords'))
                logger.info(f'Word Watcher: {keyword}')
                send_random_tenor(bot, update, keyword)




