from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import Filters, InlineQueryHandler, RegexHandler
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import telegram
import logging
import datetime
import re
import config
import yaml

from beer import beer_search_menu, beer_info, dry_score_message, wet_score_message
from gif import get_random_giphy, inlinequery
from monologue import query_limit, set_limit, handle_counter
from twitter import start_twitter_stream, send_tweets
from utils import build_menu
from weather import chuva, chuva2, scheduled_weather, send_weather
from corona import get_corona, get_covid, get_covidbr
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


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="I'm The MonologNator. I'll be back")


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
