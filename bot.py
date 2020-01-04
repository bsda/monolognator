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
import os
from operator import itemgetter
from gif import get_random_giphy, search_tenor, inlinequery, informer, lula, slough, get_random_tenor, nuclear, freakout
from monologue import query_limit, set_limit, handle_counter
from weather import get_weather, chance_of_rain_today, chuva, chuva2, scheduled_weather, send_weather

cfg = config.cfg()


logging.basicConfig(level=cfg.get('loglevel', 'INFO'),
                    format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

counter = {}
msg_limit = {}
my_chat_id = 113426151
gif_path = './gifs/'




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
    regex = re.compile('(lula|informer|slough|vai ficar tudo bem|calma cara)')
    msg = update.message.text.lower()
    for m in regex.findall(msg):
        if m == 'vai ficar tudo bem':
            m = 'nuclear'
        elif m == 'calma cara':
            m = 'freakout'
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
    method = cfg.get('update-method') or 'polling'
    token = os.getenv('telegram_token')
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
    word_watcher_regex = re.compile('.*(lula|informer|slough|vai ficar tudo bem|calma cara).*', re.IGNORECASE)
    updater.dispatcher.add_handler(RegexHandler(word_watcher_regex, word_watcher))
    # apocalex = re.compile('.*(vai ficar tudo bem).*', re.IGNORECASE)
    # updater.dispatcher.add_handler(RegexHandler(apocalex, send_nuclear))

    updater.dispatcher.add_handler(CallbackQueryHandler(beer_info))
    updater.dispatcher.add_error_handler(error)
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_counter))
    j = updater.job_queue
    daily_job = j.run_daily(scheduled_weather, time=datetime.time(6))
    if method == 'polling':
        updater.start_polling(clean=True)
    else:
        webhook_url = cfg.get('webhook-url')
        updater.start_webhook(listen='0.0.0.0',
                              port='8080',
                              url_path=token)
        logger.info(f'Setting webhook url to: {webhook_url}/{token}')
        updater.bot.set_webhook(f'{webhook_url}/{token}')
    logger.info('Starting Monolognator...')
    updater.idle()


if __name__ == '__main__':
    main()
