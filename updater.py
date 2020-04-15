
import logging
import datetime
import re
import config
import yaml
import gif
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import Filters, InlineQueryHandler, RegexHandler
from telegram.ext import CallbackQueryHandler
from beer import beer_search_menu, beer_info, dry_score_message, wet_score_message
from gif import get_random_giphy, inlinequery, word_watcher_gif, word_watcher_regex
from monologue import query_limit, set_limit, handle_counter
from movies import movie_search_menu, movie_info
from twitter import start_twitter_stream, send_tweets
from weather import chuva, chuva2, scheduled_weather, send_weather
from corona import get_corona, get_covid, get_covidbr
from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)

cfg = config.cfg()

logger = logging.getLogger(__name__)

counter = {}
msg_limit = {}
group_id = cfg.get('group_id')
my_chat_id = cfg.get('my_chat_id')


def get_updater():
    token = cfg.get('telegram_token')
    updater = Updater(token, request_kwargs={'read_timeout': 6, 'connect_timeout': 7})
    updater = get_updater()
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
    updater.dispatcher.add_handler(CommandHandler('add_alias', gif.add_alias))

    updater.dispatcher.add_handler(InlineQueryHandler(inlinequery))
    # word_watcher_regex = re.compile(f'.*{"|".join([i for i in gifs.keys()])}.*', re.IGNORECASE)
    updater.dispatcher.add_handler(RegexHandler(word_watcher_regex(), word_watcher_gif))
    updater.dispatcher.add_handler(CallbackQueryHandler(beer_info, pattern='beer'))
    updater.dispatcher.add_handler(CallbackQueryHandler(movie_info, pattern='^movie'))

    updater.dispatcher.add_error_handler(error)
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_counter))
    j = updater.job_queue
    daily_job = j.run_daily(scheduled_weather, time=datetime.time(6))
    tweet_job = j.run_repeating(send_tweets, interval=60, first=20)
    return updater


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="I'm The MonologNator. I'll be back")


def ping(bot, update):
    gif = get_random_giphy(keyword='pong')
    bot.send_document(chat_id=update.message.chat_id,
                      document=gif, timeout=100)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)
    bot.send_message(chat_id=my_chat_id,
                      text=error, timeout=100)

def error_callback(bot, update, error):
    try:
        raise error
    except Unauthorized as e:
        # remove update.message.chat_id from conversation list
        logger.error('Update "%s" caused error "%s"', update, e)
    except BadRequest as e:
        # handle malformed requests - read more below!
        logger.error('Update "%s" caused error "%s"', update, e)
    except TimedOut as e:
        # handle slow connection problems
        logger.error('Update "%s" caused error "%s"', update, e)
    except NetworkError as e:
        # handle other connection problems
        logger.error('Update "%s" caused error "%s"', update, e)
    except ChatMigrated as e:
        # the chat_id of a group has changed, use e.new_chat_id instead
        logger.error('Update "%s" caused error "%s"', update, e)
    except TelegramError as e:
        # handle all other telegram related errors
        logger.error('Update "%s" caused error "%s"', update, e)




