import logging
import datetime
import config
import yaml
import gif
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import Filters, InlineQueryHandler, RegexHandler
from telegram.ext import CallbackQueryHandler
from beer import beer_search_menu, beer_info, dry_score_message, wet_score_message
from monologue import query_limit, set_limit, handle_counter
from movies import movie_search_menu, movie_info
from twitter import start_twitter_stream, send_tweets
from weather import chuva, chuva2, scheduled_weather, send_weather
from corona import get_corona, get_covid, get_covidbr
from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)


cfg = config.cfg()
with open('gifs.yml') as f:
    gifs = yaml.load(f, Loader=yaml.FullLoader)

logger = logging.getLogger(__name__)

counter = {}
msg_limit = {}
group_id = cfg.get('group_id')
my_chat_id = cfg.get('my_chat_id')


def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id,
                     text="I'm The MonologNator. I'll be back")


def ping(update, context):
    img = gif.get_random_giphy(keyword='pong')
    context.bot.send_document(chat_id=update.message.chat_id,
                      document=img, timeout=100)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    context.bot.send_message(chat_id=my_chat_id, text=context.error, timeout=100)


def error_callback(update, context):
    try:
        context.bot.send_message(chat_id=my_chat_id, text=context.error, timeout=100)
        raise context.error
    except Unauthorized as e:
        # remove update.message.chat_id from conversation list
        logger.error('Update "%s" caused error "%s"', update, e)
        context.bot.send_message(chat_id=my_chat_id, text=context.error, timeout=100)
    except BadRequest as e:
        # handle malformed requests - read more below!
        logger.error('Update "%s" caused error "%s"', update, e)
        context.bot.send_message(chat_id=my_chat_id, text=context.error, timeout=100)
    except TimedOut as e:
        # handle slow connection problems
        logger.error('Update "%s" caused error "%s"', update, e)
        context.bot.send_message(chat_id=my_chat_id, text=context.error, timeout=100)

    except NetworkError as e:
        # handle other connection problems
        logger.error('Update "%s" caused error "%s"', update, e)
        context.bot.send_message(chat_id=my_chat_id, text=context.error, timeout=100)

    except ChatMigrated as e:
        # the chat_id of a group has changed, use e.new_chat_id instead
        logger.error('Update "%s" caused error "%s"', update, e)
        context.bot.send_message(chat_id=my_chat_id, text=context.error, timeout=100)

    except TelegramError as e:
        # handle all other telegram related errors
        logger.error('Update "%s" caused error "%s"', update, e)
        context.bot.send_message(chat_id=my_chat_id, text=context.error, timeout=100)



def main():
    method = cfg.get('update-method') or 'polling'
    token = cfg.get('telegram_token')
    logging.basicConfig(level=cfg.get('loglevel', 'INFO'),
                        format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
    updater = Updater(token, use_context=True)
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
    # GIF handlers
    updater.dispatcher.add_handler(CommandHandler('list_alias', gif.get_aliases))
    updater.dispatcher.add_handler(CommandHandler('list_aliases', gif.list_aliases))
    updater.dispatcher.add_handler(CommandHandler('add_alias', gif.add_alias))
    updater.dispatcher.add_handler(InlineQueryHandler(gif.inlinequery))
    updater.dispatcher.add_handler(MessageHandler(Filters.regex(gif.word_watcher_regex()), gif.word_watcher_gif))
    updater.dispatcher.add_handler(CallbackQueryHandler(beer_info, pattern='beer'))
    updater.dispatcher.add_handler(CallbackQueryHandler(movie_info, pattern='^movie'))

    updater.dispatcher.add_error_handler(error_callback)
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_counter))
    j = updater.job_queue
    daily_job = j.run_daily(scheduled_weather, time=datetime.time(6))
    tweet_job = j.run_repeating(send_tweets, interval=60, first=20)
    start_twitter_stream()
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
