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
import config
import yaml
import covid
from operator import itemgetter
from gif import get_random_giphy, inlinequery
from monologue import query_limit, set_limit, handle_counter
from twitter import start_twitter_stream, tqueue
from utils import build_menu, emojify
from weather import chuva, chuva2, scheduled_weather, send_weather
import corona
import movies

cfg = config.cfg()


logger = logging.getLogger(__name__)

counter = {}
msg_limit = {}
group_id = cfg.get('group_id')
my_chat_id = cfg.get('my_chat_id')

with open('filters.yml') as f:
    twitter_filters = yaml.load(f, Loader=yaml.FullLoader)['users']



# Authenticate to Twitter


def send_tweets(bot, update):
    logger.info('Checking queue')
    q = tqueue
    logger.info(f'Queue sized when reading: {q.qsize()}')
    while not q.empty():
        tweet = q.get()
        url = f'https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}'
        if url:
            logger.info(f'Sending tweet from {tweet.user.screen_name}')
            bot.send_message(chat_id=group_id, text=url)


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="I'm The MonologNator. I'll be back")


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
                                            callback_data=f'beer,{b["bid"]}'))
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=1))
    update.message.reply_text('Which one do you mean?', reply_markup=reply_markup,
                              remove_keyboard=True)


def movie_search_menu(bot, update):
    search = update.message.text.split('/movie ')[1]
    movie = movies.search(search)
    buttons = list()
    for m in movie:
        buttons.append(InlineKeyboardButton(f'{m.data.get("title")} - {m.data.get("year")}',
                       callback_data=f'movie,{m.movieID}'))
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=2))
    update.message.reply_text('Which one do you mean?', reply_markup=reply_markup,
                              remove_keyboard=True)

def movie_info(bot, update):
    query = update.callback_query
    mid = query.message.message_id
    cid = query.message.chat_id
    bot.delete_message(chat_id=cid, message_id=mid)
    movieid = query.data.split(',')[1]
    md = movies.movie(movieid)
    directors = [i.data.get('name') for i in md.data.get('directors')]
    cast = [i.data.get('name') for i in md.data.get('cast')[:4]]
    countries = [i for i in md.data.get('countries')]
    air_date = md.data.get('original air date')
    rating = md.data.get('rating')
    votes = md.data.get('votes')
    cover = md.data.get('cover url')
    plot = md.data.get('plot')[0]
    # if len(plot) > 1:
    #     plot = plot[1]
    # else:
    #     plot = plot[0]
    title = md.data.get('title')
    year = md.data.get('year')
    box_office = md.data.get('box office')
    if box_office:
        budget = box_office.get('Budget')
        gross = box_office.get('Cumulative Worldwide Gross')
    message = f'*{title} - {year} - {", ".join(countries)} *\n'
    message += f'*Rating:* {rating}, *Votes:* {votes}\n'
    message += f"*Directors:* {', '.join(directors)}\n"
    message += f"*Cast:* {', '.join(cast)}\n"
    if box_office:
        message += f"*Budget:* {budget}, *Gross:* {gross},\n"
    message += "*Plot:*\n\n"
    message += f"{plot}\n\n"
    message += f'{cover}\n\n'

    logger.info(f'Sending {title}')
    bot.send_message(chat_id=cid,
                     text=message, parse_mode=telegram.ParseMode.MARKDOWN,
                     timeout=150)

def beer_info(bot, update):
    query = update.callback_query
    mid = query.message.message_id
    cid = query.message.chat_id
    bot.delete_message(chat_id=cid, message_id=mid)
    bid = query.data.split(',')[1]
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
    text = corona.corona_uk()
    if text:
        bot.send_message(chat_id=group_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)


def get_corona(bot, update):
    text = update.message.text.split('/corona ')
    user = update.message.from_user.first_name
    l = len(text)
    if len(text) > 1:
        countries = text[1].split(',')
        countries = [i.lower().replace(' ', '') for i in countries]
        logger.info(f'{user} requested corona for {countries}')
        text = corona.corona(countries)
    else:
        text = corona.corona()
        logger.info(f'{user} requested corona')
    if text:
        bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=telegram.ParseMode.HTML)


def get_covid(bot, update):
    text = update.message.text.split('/covid ')
    user = update.message.from_user.first_name
    l = len(text)
    if l == 2:
        country = text[1]
        logger.info(f'{user} requested covid for {country}')
        text = covid.detailed(country)
    elif l > 2:
        countries = text[1].split(',')
        countries = [i.lower().replace(' ', '') for i in countries]
        logger.info(f'{user} requested corona for {countries}')
        text = covid.covid(countries)
    else:
        text = covid.covid()
        logger.info(f'{user} requested covid')
    if text:
        bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=telegram.ParseMode.HTML)


def get_covidbr(bot, update):
    user = update.message.from_user.first_name
    text = covid.br()
    logger.info(f'{user} requested covid BR')
    if text:
        bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode=telegram.ParseMode.HTML)


def ping(bot, update):
    gif = get_random_giphy(keyword='pong')
    bot.send_document(chat_id=update.message.chat_id,
                      document=gif, timeout=100)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    logging.basicConfig(level=cfg.get('loglevel', 'INFO'),
                        format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
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
    updater.dispatcher.add_handler(CommandHandler('corona', get_corona))
    updater.dispatcher.add_handler(CommandHandler('covid', get_covid))
    updater.dispatcher.add_handler(CommandHandler('covidbr', get_covidbr))
    updater.dispatcher.add_handler(CommandHandler('movie', movie_search_menu))
    updater.dispatcher.add_handler(InlineQueryHandler(inlinequery))
    word_watcher_regex = re.compile('.*(lula|informer|slough|vai ficar tudo bem|calma cara|999London).*', re.IGNORECASE)
    updater.dispatcher.add_handler(RegexHandler(word_watcher_regex, word_watcher))
    # apocalex = re.compile('.*(vai ficar tudo bem).*', re.IGNORECASE)
    # updater.dispatcher.add_handler(RegexHandler(apocalex, send_nuclear))

    updater.dispatcher.add_handler(CallbackQueryHandler(beer_info, pattern='beer'))
    updater.dispatcher.add_handler(CallbackQueryHandler(movie_info, pattern='^movie'))

    # updater.dispatcher.add_error_handler(error)
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_counter))
    j = updater.job_queue
    daily_job = j.run_daily(scheduled_weather, time=datetime.time(6))
    tweet_job = j.run_repeating(send_tweets, interval=60, first=20)
    # corona_job = j.run_repeating(corona_update, interval=1200, first=20)
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
