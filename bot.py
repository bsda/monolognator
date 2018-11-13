from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler
from telegram import MessageEntity
import telegram
import logging
import os
import time
import datetime
import beer
import links
from gif import get_random_giphy, search_tenor, inlinequery
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
    message += '*___Ratebeer:___*\n'
    message += f'*{rating["r_name"]}* by {rating["r_brewery"]}\n'
    message += f'*{rating["r_style"]}*, abv: {rating["r_abv"]}%\n'
    message += f'Rating: *{rating["r_rating"]}*, Count: {rating["r_count"]},' \
               f' Style Score: {rating["r_style_score"]}\n'
    image = rating['image']
    bot.send_photo(chat_id=update.message.chat_id, photo=image)
    try:
        bot.send_message(chat_id=update.message.chat_id,
                         text=message, parse_mode=telegram.ParseMode.MARKDOWN,
                         timeout=150)
    except TimeoutError:
        time.sleep(2)
        bot.send_message(chat_id=update.message.chat_id,
                         text=message, parse_mode=telegram.ParseMode.MARKDOWN,
                         timeout=150)


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
    updater.dispatcher.add_handler(CommandHandler('beer', beer_rating))
    updater.dispatcher.add_handler(InlineQueryHandler(inlinequery))
    updater.dispatcher.add_error_handler(error)
    updater.dispatcher.add_handler(MessageHandler(
        Filters.text & (Filters.entity(MessageEntity.URL) |
                        Filters.entity(MessageEntity.TEXT_LINK)), links.counter))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_counter))
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
                              webhook_url=f'{webhook_url}/{token}')
    logger.info('Starting Monolognator...')
    updater.idle()


if __name__ == '__main__':
    main()
