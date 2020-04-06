from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import Filters, InlineQueryHandler, RegexHandler
from telegram.ext import CallbackQueryHandler
import logging
import datetime
import re
import config
import yaml

from beer import beer_search_menu, beer_info, dry_score_message, wet_score_message
from gif import get_random_giphy, inlinequery
from monologue import query_limit, set_limit, handle_counter
from movies import movie_search_menu, movie_info
from twitter import start_twitter_stream, send_tweets
from weather import chuva, chuva2, scheduled_weather, send_weather
from corona import get_corona, get_covid, get_covidbr

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
