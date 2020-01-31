from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import Filters, InlineQueryHandler, RegexHandler
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import telegram
import logging
import datetime
import beer
import re
import random
import flag
import pycountry
import config
import tweepy
import yaml
import json
from operator import itemgetter
from gif import get_random_giphy, search_tenor, inlinequery, informer, lula, slough, get_random_tenor, nuclear, freakout, london999
from monologue import query_limit, set_limit, handle_counter
from weather import get_weather, chance_of_rain_today, chuva, chuva2, scheduled_weather, send_weather
import corona
import twitter
import string

cfg = config.cfg()


logging.basicConfig(level=cfg.get('loglevel', 'INFO'),
                    format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

counter = {}
msg_limit = {}
group_id = cfg.get('group_id')
my_chat_id = cfg.get('my_chat_id')

with open('filters.yml') as f:
    twitter_filters = yaml.load(f, Loader=yaml.FullLoader)['users']


# Authenticate to Twitter
def start_twitter_stream():
    auth = tweepy.OAuthHandler(cfg.get('twitter_api_key'),
                               cfg.get('twitter_api_secret'))
    auth.set_access_token(cfg.get('twitter_token'),
                          cfg.get('twitter_token_secret'))

    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    tweets_listener = twitter.Stream(api)
    stream = tweepy.Stream(api.auth, tweets_listener)
    stream.filter(follow=[str(a) for a in twitter_filters.keys()], is_async=True)


def filter_tweet(tweet):
    # logger.info('Filtering tweets')
    user_id = tweet.user.id
    name = tweet.user.screen_name
    text = tweet.text
    logger.debug(f'Tweet from {user_id}, {name}')
    if user_id in twitter_filters:
        user = twitter_filters.get(tweet.user.id)
        user_filter = user.get('filter')
        filter_type = user.get('type')
        text = text.lower()
        new_text = re.sub(r'http\S+', '', text)
        regex = re.compile('[%s]' % re.escape(string.punctuation))
        new_text = regex.sub('', new_text).lower()
        text_list = new_text.split()
        logger.info(f'TWEET FROM {name}: {text}')
        if user_filter:
            if filter_type == 'string':
                if any(word.lower() in text_list for word in user_filter):
                    logger.info(f'Filter match for {name}, type:{filter_type}')
                    logger.info(f'Word: {text_list}')
                    return f'https://twitter.com/{name}/status/{tweet.id}'
                else:
                    return None
            if filter_type == 'regex':
                rex = re.compile(user_filter)
                if rex.findall(text, re.IGNORECASE):
                    logger.info(f'Filter match for {name}, type:{filter_type}')
                    logger.info(f'Word: {text_list}')
                    return f'https://twitter.com/{name}/status/{tweet.id}'
                else:
                    return None
        logger.info(f'User match for {name}, empty filter')
        return f'https://twitter.com/{name}/status/{tweet.id}'
    # logger.info(f'Dropping tweet from {name}, {user_id}, {text}, ')
    return None


def send_tweets(bot, update):
    logger.debug('Checking queue')
    q = twitter.tqueue
    while not q.empty():
        tweet = q.get()
        url = filter_tweet(tweet)
        if url:
            logger.info(f'Sending tweet from {tweet.user.screen_name}')
            bot.send_message(chat_id=group_id, text=url)


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="I'm The MonologNator. I'll be back")


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


def beer_search_menu(bot, update):
    if update.message.text.startswith('/beer'):
        search = update.message.text.split('/beer ')[1]
        beers = beer.search_untappd(search)
    elif update.message.text.startswith('/homebrew'):
        search = update.message.text.split('/homebrew ')[1]
        beers = beer.search_untappd(search, homebrew=True)
    buttons = list()
    for b in beers:
        emoji = emojify(b['country'])
        buttons.append(InlineKeyboardButton(f'{emoji}  {b["name"]} by {b["brewery"]} - ({b["checkin_count"]}) checkins',
                                            callback_data=b['bid']))
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=1))
    update.message.reply_text('Which one do you mean?', reply_markup=reply_markup,
                              remove_keyboard=True)


def beer_info(bot, update):
    query = update.callback_query
    mid = query.message.message_id
    cid = query.message.chat_id
    bot.delete_message(chat_id=cid, message_id=mid)
    bid = query.data
    info = beer.get_untappd_beer(bid)
    emoji = emojify(info['country'])
    message = f'<a href="http://untappd.com/beer/{info["bid"]}"> {info["name"]}</a> by {info["brewery"]} {emoji}\n'
    message += f'<b>{info["style"]}, abv:</b> {info["abv"]}%\n'
    message += f'<b>Rating:</b> {info["rating"]}\n'
    if info['label']:
        photo = info['label']
    else:
        try:
            photo = random.choice(info['photos'])
        except IndexError:
            photo = 'https://untappd.akamaized.net/site/assets/images/temp/badge-beer-default.png'
    bot.send_photo(chat_id=query.message.chat_id,
                   caption=message,
                   parse_mode=telegram.ParseMode.HTML,
                   photo=photo)


def dry_score_message(bot, update):
    users = cfg.get('untappd-users')
    score = beer.get_dry_scores(users)
    sorted_score = sorted(score, key=itemgetter('days'), reverse=True)
    message = '*Current Dry Scores*:\n\n'
    sorted_score[0]['brewery'] = f"{sorted_score[0]['brewery']} 🏆"
    for s in sorted_score:
        days_s = 'day' if s['days'] == 1 else 'days'
        message += f" `{s['user']}`: *{s['days']}* - *{s['beer']}* by {s['brewery']}\n"
    bot.send_message(chat_id=update.message.chat_id,
                     text=message, parse_mode=telegram.ParseMode.MARKDOWN,
                     timeout=150)


def wet_score_message(bot, update):
    users = cfg.get('untappd-users')
    wet_score = beer.get_wet_scores(users)
    sorted_score = sorted(wet_score, key=itemgetter('score'), reverse=True)
    message = '*Last Week Wet Scores*:\n\n'
    sorted_score[0]['user'] = f"{sorted_score[0]['user']} 🏆"
    for s in sorted_score:
        message += f" `{s['user']}`: *{s['score']}* check-ins\n"
    bot.send_message(chat_id=update.message.chat_id,
                     text=message, parse_mode=telegram.ParseMode.MARKDOWN,
                     timeout=150)


def word_watcher(bot, update):
    regex = re.compile('(lula|informer|slough|vai ficar tudo bem|calma cara|999London)', re.IGNORECASE)
    msg = update.message.text.lower()
    logger.info(f'Start word watcher with {msg}')
    a = regex.findall(msg)
    for m in regex.findall(msg):
        if m == 'vai ficar tudo bem':
            m = 'nuclear'
        elif m == 'calma cara':
            m = 'freakout'
        elif m == '999london':
            m = 'london999'
        logger.info(f'word watcher: {m}')
        method = globals()[m]
        method(bot, update)


def corona_update(bot, update):
    text = corona.status()
    if text:
        bot.send_message(chat_id=group_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)


def ping(bot, update):
    gif = get_random_giphy(keyword='pong')
    bot.send_document(chat_id=update.message.chat_id,
                      document=gif, timeout=100)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    start_twitter_stream()
    method = cfg.get('update-method') or 'polling'
    token = cfg.get('telegram_token')
    updater = Updater(token, request_kwargs={'read_timeout': 6, 'connect_timeout': 7})
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('ping', ping))
    updater.dispatcher.add_handler(CommandHandler('limit', query_limit))
    updater.dispatcher.add_handler(CommandHandler('set_limit', set_limit))
    updater.dispatcher.add_handler(CommandHandler('weather', send_weather))
    updater.dispatcher.add_handler(CommandHandler('chuva', chuva))
    updater.dispatcher.add_handler(CommandHandler('chuva2', chuva2))
    updater.dispatcher.add_handler(CommandHandler('beer', beer_search_menu))
    updater.dispatcher.add_handler(CommandHandler('homebrew', beer_search_menu))
    updater.dispatcher.add_handler(CommandHandler('beer2', beer_search_menu))
    updater.dispatcher.add_handler(CommandHandler('dry', dry_score_message))
    updater.dispatcher.add_handler(CommandHandler('wet', wet_score_message))
    updater.dispatcher.add_handler(InlineQueryHandler(inlinequery))
    word_watcher_regex = re.compile('.*(lula|informer|slough|vai ficar tudo bem|calma cara|999London).*', re.IGNORECASE)
    updater.dispatcher.add_handler(RegexHandler(word_watcher_regex, word_watcher))
    # apocalex = re.compile('.*(vai ficar tudo bem).*', re.IGNORECASE)
    # updater.dispatcher.add_handler(RegexHandler(apocalex, send_nuclear))

    updater.dispatcher.add_handler(CallbackQueryHandler(beer_info))
    updater.dispatcher.add_error_handler(error)
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_counter))
    j = updater.job_queue
    daily_job = j.run_daily(scheduled_weather, time=datetime.time(6))
    tweet_job = j.run_repeating(send_tweets, interval=60, first=20)
    corona_job = j.run_repeating(corona_update, interval=1200, first=20)
    if method == 'polling':
        updater.start_polling(clean=True)
    else:
        webhook_url = cfg.get('webhook-url')
        webhook_url = webhook_url + '/' + token
        updater.start_webhook(listen='0.0.0.0',
                              port='8080',
                              url_path=token)
        logger.info(f'Setting webhook url to: {webhook_url}')
        updater.bot.set_webhook(url=webhook_url)
    logger.info('Starting Monolognator...')
    updater.idle()


if __name__ == '__main__':
    main()
