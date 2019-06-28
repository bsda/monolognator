from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, RegexHandler
from telegram import MessageEntity
import telegram
import logging
import os
import time
import datetime
import beer
import re
import json
from operator import itemgetter
from gif import get_random_giphy, search_tenor, inlinequery, informer, lula
from monologue import query_limit, set_limit, handle_counter
from weather import get_weather, chance_of_rain_today, chuva, chuva2, scheduled_weather, send_weather

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

counter = {}
msg_limit = {}
my_chat_id = 113426151
gif_path = './gifs/'


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="I'm The MonologNator. I'll be back")


def beer_rating(bot, update):
    search = update.message.text.split('/beer ')[1]
    rating = beer.beer(search)
    message = '*___Untappd:___*\n'
    message += f'*{rating["u_name"]}* by {rating["u_brewery"]}\n'
    message += f'*{rating["u_style"]}*, abv: {rating["u_abv"]}%\n'
    message += f'Rating: *{rating["u_rating"]}*, Count: {rating["u_count"]}\n\n'
    try:
        bot.send_message(chat_id=update.message.chat_id,
                         text=message, parse_mode=telegram.ParseMode.MARKDOWN,
                         timeout=150)
    except TimeoutError:
        time.sleep(2)
        bot.send_message(chat_id=update.message.chat_id,
                         text=message, parse_mode=telegram.ParseMode.MARKDOWN,
                         timeout=150)


def dry_score_message(bot, update):
    users = json.loads(os.environ['untappd_users'])
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
    users = json.loads(os.environ['untappd_users'])
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
    regex = re.compile('(lula|informer)')
    msg = update.message.text.lower()
    for m in regex.findall(msg):
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
    method = os.getenv('update_method') or 'polling'
    token = os.getenv('telegram_token')
    updater = Updater(token, request_kwargs={'read_timeout': 6, 'connect_timeout': 7})
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('ping', ping))
    updater.dispatcher.add_handler(CommandHandler('limit', query_limit))
    updater.dispatcher.add_handler(CommandHandler('set_limit', set_limit))
    updater.dispatcher.add_handler(CommandHandler('weather', send_weather))
    updater.dispatcher.add_handler(CommandHandler('chuva', chuva))
    updater.dispatcher.add_handler(CommandHandler('chuva2', chuva2))
    # updater.dispatcher.add_handler(CommandHandler('chuva3', scheduled_chuva))
    updater.dispatcher.add_handler(CommandHandler('beer', beer_rating))
    updater.dispatcher.add_handler(CommandHandler('dry', dry_score_message))
    updater.dispatcher.add_handler(CommandHandler('wet', wet_score_message))
    updater.dispatcher.add_handler(InlineQueryHandler(inlinequery))
    word_watcher_regex = re.compile('.*(lula|informer).*', re.IGNORECASE)
    # informer_regex = re.compile('.*informer.*', re.IGNORECASE)
    # lula_regex = re.compile('.*lula.*', re.IGNORECASE)
    # updater.dispatcher.add_handler(RegexHandler(informer_regex, informer))
    # updater.dispatcher.add_handler(RegexHandler(lula_regex, lula))
    updater.dispatcher.add_handler(RegexHandler(word_watcher_regex, word_watcher))
    updater.dispatcher.add_error_handler(error)
    # updater.dispatcher.add_handler(MessageHandler(
    #     Filters.text & (Filters.entity(MessageEntity.URL) |
    #                     Filters.entity(MessageEntity.TEXT_LINK)), links.counter))
    updater.dispatcher.add_handler(MessageHandler(Filters.text & (~ Filters.reply), handle_counter))
    j = updater.job_queue
    daily_job = j.run_daily(scheduled_weather, time=datetime.time(5))
    if method == 'polling':
        updater.start_polling(clean=True)
    else:
        webhook_url = os.getenv('webhook_url')
        updater.start_webhook(listen='0.0.0.0',
                              port=8443,
                              url_path=token,
                              key='private.key',
                              cert='cert.pem',
                              webhook_url=f'{webhook_url}/{token}',
                              clean=True)
    logger.info('Starting Monolognator...')
    updater.idle()


if __name__ == '__main__':
    main()
