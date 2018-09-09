from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler
import telegram
import random
import logging
import os
import re
import requests
import uuid
import time
import datetime
from geopy import Nominatim




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


def query_limit(bot, update):
    user = update.message.from_user.id
    chat = update.message.chat_id
    if update.message.chat_id not in msg_limit:
        random_limit(update)
    logger.info(f'Limit query on {update.message.chat.title}'
                f' by {update.message.from_user.first_name}.'
                f' Limit: {msg_limit[update.message.chat_id]}')
    update.message.reply_text(f"Current limit: {get_limit(update.message.chat_id)}\n"
                              f"Your count: {get_count(chat, user)}")
    logger.info('================================================')


def random_limit(update):
    global msg_limit
    msg_limit[update.message.chat_id] = random.randint(8, 12)
    # bot.send_message(chat_id=my_chat_id,
    #                  text=f'New random limit set on {update.message.chat.title}: {msg_limit[update.message.chat_id]}')
    logger.info(f'Random limit of {msg_limit[update.message.chat_id]} set on {update.message.chat.title}')
    logger.info('================================================')
    return msg_limit[update.message.chat_id]


def set_limit(bot, update):
    logger.debug(update.message.text)
    global msg_limit
    msg = update.message.text
    if not re.match(r'^/set_limit [0-9]+$', msg):
        update.message.reply_text("Nah... I didn't get that. Use a number only, stupid!")
    else:
        msg_limit[update.message.chat_id] = int(re.findall('[0-9]+', msg)[0])
        logger.info(f'New Limit set by {update.message.from_user.first_name}'
                    f' on {update.message.chat.title}: {msg_limit[update.message.chat_id]}')
        logger.info('================================================')
        bot.send_message(chat_id=my_chat_id,
                         text=f'Manual limit set on {update.message.chat.title}'
                              f' by {update.message.from_user.first_name}: {msg_limit[update.message.chat_id]}')


def inlinequery(bot, update):
    """Handle the inline query."""
    query = update.inline_query.query
    print(query)
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
    giphy_token = os.getenv('giphy_token')
    params = {'api_key': giphy_token, 'rating': 'r',
              'q': keyword, 'limit': 50, 'offset': offset}
    re = requests.get(f'https://api.giphy.com/v1/gifs/search', params=params)
    for g in re.json()['data']:
        gifs.append({'id': g['id'], 'url': g['images']['downsized_medium']['url'],
                     'thumb_url': g['images']['preview_gif']['url']})
    return gifs


def search_tenor(keyword, offset=0):
    gifs = []
    tenor_token = os.getenv('tenor_token')
    params = {'key': tenor_token, 'media_filter': 'minimal',
              'q': keyword, 'limit': 40, 'pos': offset}
    re = requests.get(f'https://api.tenor.com/v1/search', params=params)
    for g in re.json()['results']:
        for m in g['media']:
            gifs.append({'id': g['id'], 'url': m['gif']['url'],
                         'thumb_url': m['gif']['preview']})
    return gifs


def get_random_tenor(keyword):
    tenor_token = os.getenv('tenor_token')
    params = {'key': tenor_token, 'media_filter': 'minimal',
              'q': keyword, 'limit': 50, 'pos': random.choice(range(300))}
    # print(params)
    re = requests.get(f'https://api.tenor.com/v1/random', params=params)
    gif = random.choice(re.json()['results'])['media'][0]['mediumgif']['url']
    print(gif)
    return gif


def send_random_tenor(bot, update, keyword):
    gif = get_random_tenor(keyword)
    bot.send_document(chat_id=update.message.chat_id,
                      document=gif, timeout=100)


def get_random_giphy(keyword=None):
    giphy_token=os.getenv('giphy_token')
    # offset = 0
    # gifs = list()
    params = {'api_key': giphy_token, 'rating': 'r'}
    if keyword:
        params.update({'tag': keyword})
    # for i in range(5):
    #     gifs.extend(search_tenor(keyword, offset=offset))
    #     offset+=40


    re = requests.get(f'https://api.giphy.com/v1/gifs/random', params=params)
    gif = re.json()['data']['images']['downsized_medium']['url']
    logger.info(f'Sending gif: {gif}')
    # gif = random.choice(gifs)['url']
    return gif


def get_weather(location='London'):
    logger.info(f'Getting weather for {location}')
    geo = Nominatim(user_agent='Monolognator')
    loc = geo.geocode(location)
    latlon = f'{loc.latitude}, {loc.longitude}'
    # location = '51.4975,-0.1357'
    key = os.getenv('darksky_token')
    params = {'units': 'si'}
    re = requests.get(f'https://api.darksky.net/forecast/{key}/{latlon}', params=params)
    results = re.json()
    return results


def weather(bot, update, location=None):
    """
    Currenty:
    ['currently']['time']
    ['currently']['summary']
    ['currently']['precipProbability']
    ['currently']['temperature']
    Next Hour:
    ['minutely']['summary']
    Day:
    ['hourly']['summary']
    for i in ['hourly']['data']
        i['precipProbability'] - get highest
        i['time']
        i['summary']
    Weekly:
    ['daily']['summary']
    for i in ['daily']['data']
        i['time']
        i['summary']
        i['precipProbability']
        i['temperatureHigh']
        i['temperatureLow']
    :return:
    """
    if update.message.text == '/weather':
        location = 'London'
    else:
        location = update.message.text.split('/weather ')[1]
    results = get_weather(location)
    # getting the highest chance of precipitation in the next 24h
    highest_chance_of_rain = 0
    day_summary = {}
    for i in results['hourly']['data']:
        if i['precipProbability'] > 0 and i['precipProbability'] > highest_chance_of_rain:
            highest_chance_of_rain = i['precipProbability']
            day_summary = {'chance': highest_chance_of_rain * 100,
                           'time': i['time'], 'summary': i['summary']}

    message = f'''Good Morning {update.message.chat.title}, here is your daily forecast:
    
    *Current Conditions:*
    {results['currently']['summary']}
    Chance of Rain: {results['currently']['precipProbability'] * 100}%, Current Temperature: {results['currently']['temperature']}C
    
    *Summary of conditions for the next hour:*
    {results['minutely']['summary']}
    
    *Conditions for the rest of the day:*
    {results['hourly']['summary']}
    Highest Chance of Rain: {day_summary['chance']}% at {time.strftime('%l%p', time.localtime(day_summary['time']))}
    
    *Summary of conditions for the rest of the week:*
    {results['daily']['summary']}'''

    bot.send_message(chat_id=update.message.chat_id,
                     text=f'*Monolognator Weather Report powered by darksky.net*:\n\n{message}',
                     parse_mode=telegram.ParseMode.MARKDOWN)


def vai_chover2():
    results = get_weather()
    # getting the highest chance of precipitation in the next 24h
    rain_threshold = 11
    highest_chance = 0
    for i in results['hourly']['data']:
        day = int(time.strftime('%d', time.localtime(i['time'])))
        hour = int(time.strftime('%H', time.localtime(i['time'])))
        chance = i['precipProbability'] * 100
        if not 6 <= hour <= 20:
            continue
        if chance > highest_chance:
            highest_chance = chance
    if highest_chance <= 15:
        return 'Nao vai chover'
    elif 15 < highest_chance <= 30:
        return 'Pode chover'
    elif 30 < highest_chance <= 50:
        return 'Provavelmente vai chover'
    return 'Vai chover'



def vai_chover():
    results = get_weather()
    # getting the highest chance of precipitation in the next 24h
    rain_threshold = 11
    for i in results['hourly']['data']:
        day = int(time.strftime('%d', time.localtime(i['time'])))
        hour = int(time.strftime('%H', time.localtime(i['time'])))
        chance = i['precipProbability'] * 100
        if not 6 <= hour <= 20:
            continue
        if chance >= rain_threshold:
            return 'Vai chover'
    return 'Nao vai chover'


def chuva(bot, update, chat_id=None):
    if chat_id is None:
        chat_id = update.message.chat_id
    chove = vai_chover()
    logger.info(f'Chove? {chove}')
    if chove == 'Vai chover':
        gif = get_random_giphy(keyword='sad')
    else:
        gif = get_random_giphy(keyword='happy')
    bot.send_document(chat_id=chat_id,
                      document=gif, caption=f'Bom dia, {chove} hoje', timeout=5000,
                      parse_mode=telegram.ParseMode.MARKDOWN)

    # bot.send_message(chat_id=update.message.chat_id,
    #                  text=f'Bom dia, *{vai_chover()}*',
    #                  parse_mode=telegram.ParseMode.MARKDOWN)


def chuva2(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text=f'Bom dia, *{vai_chover2()}*',
                     parse_mode=telegram.ParseMode.MARKDOWN)


def ping(bot, update):
    gif, title = get_random_giphy(keyword='pong')
    bot.send_document(chat_id=update.message.chat_id,
                      document=gif, timeout=100)


def get_random_local_gif():
    gifs = list()
    for file in os.listdir(gif_path):
        if file.endswith('.gif'):
            gifs.append(file)
    return gif_path + random.choice(gifs)


def send_local_gif(bot, update):
    bot.send_document(chat_id=update.message.chat_id,
                      document=open(get_random_local_gif(), 'rb'), timeout=500)


def delete_messages(bot, user, chat):
    # Delete messages from group
    for m in set(counter[chat][user]['msg_ids']):
        bot.delete_message(chat_id=chat, message_id=m)


def add_count(chat, user, update):
    global counter
    user_counter = counter[chat][user]
    user_counter['count'] += 1
    user_counter['msg_ids'].append(update.message.message_id)
    user_counter['msgs'].append(update.message.text)


def initialize_count(chat, user, update):
    global counter
    if chat not in counter:
        counter[chat] = {}
    counter[chat][user] = {}
    user_counter = counter[chat][user]
    user_counter['count'] = 1
    user_counter['msg_ids'] = [update.message.message_id]
    user_counter['msgs'] = [update.message.text]
    counter[chat]['latest_by'] = user


def reset_count(chat, user, update):
    global counter
    previous_user = counter[chat]['latest_by']
    logger.info(f"Resetting the counter for {previous_user} on {update.message.chat.title}")
    counter[chat].pop(previous_user)
    initialize_count(chat, user, update)


def get_count(chat, user):
    return counter[chat][user]['count']


def get_limit(chat):
    return msg_limit[chat]


def hit_limit(chat, user, update):
    if chat not in msg_limit:
        random_limit(update)
        return False
    chat_limit = get_limit(chat)

    if get_count(chat, user) == chat_limit:
        # Reset counter. limit and return True
        random_limit(update)
        return True
    return False


def monolognate(chat, user, bot, update):

    delete_messages(bot, user, chat)
    send_random_tenor(bot, update, 'tsunami')
    # Send monologue back as a single message
    bot.send_message(chat_id=update.message.chat_id,
                     text='*Monologue by {}*:\n\n`{}`'.format(
                         update.message.from_user.first_name,
                         "\n".join(counter[chat][user]['msgs'])), parse_mode=telegram.ParseMode.MARKDOWN)
    reset_count(chat, user, update)


def handle_counter(bot, update):
    user = update.message.from_user.id
    chat = update.message.chat_id
    logger.info(f'Msg on {update.message.chat.title}({chat})'
                f' from {update.message.from_user.first_name}({user}): {update.message.text}')

    # If it's a new user or the count was reset earlier
    if chat not in counter or user not in counter[chat]:
        initialize_count(chat, user, update)
    else:
        # if we seen the user before, check if previous msg was by the same user
        # if it was, increase counter and add msgs
        if user == counter[chat]['latest_by']:
            add_count(chat, user, update)
            logger.info(f'Count for {update.message.from_user.first_name}'
                        f' on {update.message.chat.title}: {get_count(chat, user)}')
            # Check if user hit  chat limit. If it did, monolognate it
            if hit_limit(chat, user, update):
                monolognate(chat, user, bot, update)
        else:
            reset_count(chat, user, update)



def scheduled_weather(bot, job):
    chove = vai_chover()
    logger.info(f'Running scheduled job: {chove}')
    if chove == 'Vai chover':
        gif = get_random_giphy(keyword='sad')
    else:
        gif = get_random_giphy(keyword='happy')
    bot.send_document(chat_id=-1001105653255,
                      document=gif, caption=f'Em Westminster, 6 da manha! Bom dia, {chove} hoje', timeout=1000,
                      parse_mode=telegram.ParseMode.MARKDOWN)



def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():

    updater = Updater(os.getenv('telegram_token'))
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('ping', ping))
    updater.dispatcher.add_handler(CommandHandler('limit', query_limit))
    updater.dispatcher.add_handler(CommandHandler('set_limit', set_limit))
    updater.dispatcher.add_handler(CommandHandler('weather', weather))
    updater.dispatcher.add_handler(CommandHandler('chuva', chuva))
    updater.dispatcher.add_handler(CommandHandler('chuva2', chuva2))
    updater.dispatcher.add_handler(InlineQueryHandler(inlinequery))
    updater.dispatcher.add_error_handler(error)
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_counter))
    j = updater.job_queue
    daily_job = j.run_daily(scheduled_weather, time=datetime.time(6))
    updater.start_polling(clean=True)
    logger.info('Starting Monolognator...')
    updater.idle()


if __name__ == '__main__':
    main()
