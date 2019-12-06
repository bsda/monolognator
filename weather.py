
import telegram
import logging
import os
import requests
import time
import datetime
from geopy import Nominatim
from gif import get_random_giphy, search_tenor, inlinequery

logger = logging.getLogger(__name__)



# WEATHER
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




def chance_of_rain_today(results):
    # only until midnight today
    logger.info('Getting chance of rain today')
    max_time = datetime.datetime.combine(datetime.datetime.today(), datetime.time.max).timestamp()
    now = datetime.datetime.now().timestamp()
    highest_chance = 0
    highest_chance_time = None
    for i in results['hourly']['data']:
        if now <= i['time'] < max_time:
            hour = time.strftime('%l%p', time.localtime(i['time']))
            chance = round(i['precipProbability'] * 100, 2)
            if chance > highest_chance:
                highest_chance = chance
                highest_chance_time = hour
    if highest_chance > 0:
        return highest_chance, highest_chance_time
    else:
        return 0, None


def vai_chover2(location):
    results = get_weather(location)
    chance_of_rain, time_of_rain = chance_of_rain_today(results)
    if chance_of_rain <= 15:
        return 'Nao vai chover', time_of_rain, chance_of_rain
    elif chance_of_rain > 15 and chance_of_rain <= 30:
        return 'Pode chover', time_of_rain, chance_of_rain
    elif chance_of_rain > 30 and chance_of_rain <= 50:
        return 'Provavelmente vai chover', time_of_rain, chance_of_rain
    return 'Vai chover', time_of_rain, chance_of_rain


def vai_chover(location):
    results = get_weather(location)
    # getting the highest chance of precipitation in the next 24h
    rain_threshold = 11
    chance_of_rain, time_of_rain = chance_of_rain_today(results)
    if chance_of_rain >= rain_threshold:
        return 'Vai chover', time_of_rain, chance_of_rain
    return 'Nao vai chover', time_of_rain, chance_of_rain


def chuva(bot, update, chat_id=None):
    if update.message.text == '/chuva':
        location = 'London'
    else:
        location = update.message.text.split('/chuva ')[1]
    if chat_id is None:
        chat_id = update.message.chat_id
    # TODO duplicate call for get_weather, need a better way to do it
    # Getting results again so we can get the max temperature for the day
    results = get_weather(location)
    # Check for alerts
    if 'alerts' in results.keys():
        alert = results['alerts'][0]['title']
        alert_time = time.strftime('%l%p', time.localtime(results['alerts'][0]['time']))
        alert_description = results['alerts'][0]['description']
    max_temp = results['daily']['data'][0]['temperatureMax']
    chove, time_of_rain, chance_of_rain = vai_chover(location)
    logger.info(f'Chove? {chove}')
    if chove == 'Vai chover':
        gif = get_random_giphy(keyword='sad')
    else:
        gif = get_random_giphy(keyword='happy')
    bot.send_document(chat_id=chat_id,
                      document=gif, caption=f'Bom dia, *{chove}* em {location} hoje '
                                            f'*({chance_of_rain}% at {time_of_rain})*.'
                                            f'\nMax Temp: *{max_temp}*C', timeout=5000,

                      parse_mode=telegram.ParseMode.MARKDOWN)
    # Send alert if there is one
    if 'alerts' in results.keys():
        bot.send_document(chat_id=chat_id,
                          document=get_random_giphy('extreme weather'),
                          caption=f'*Incoming Weather Alert for {location}*',
                          timeout=5000,
                          parse_mode=telegram.ParseMode.MARKDOWN)
        bot.send_chat_action(chat_id=chat_id, action=telegram.ChatAction.TYPING)
        time.sleep(5)
        bot.send_message(chat_id=chat_id,
                         text=f'Alerta para {location}:\n'
                              f'{alert} at {alert_time}\n\n'
                              f'{alert_description}',
                         timeout=5000)


def chuva2(bot, update, chat_id=None):
    if update.message.text == '/chuva2':
        location = 'London'
    else:
        location = update.message.text.split('/chuva2 ')[1]
    if chat_id is None:
        chat_id = update.message.chat_id
    # TODO move this somewhere else
    # Getting results again so we can get the max temperature for the day
    results = get_weather(location)
    max_temp = results['daily']['data'][0]['temperatureMax']
    chove, time_of_rain, chance_of_rain = vai_chover2(location)
    logger.info(f'Chove? {chove}')
    if chove == 'Nao vai chover':
        gif = get_random_giphy(keyword='happy')
    elif chove == 'Pode chover':
        gif = get_random_giphy(keyword='unsure')
    elif chove == 'Provavelmente vai chover':
        gif = get_random_giphy(keyword='probably')
    else:
        gif = get_random_giphy(keyword='sad')
    bot.send_document(chat_id=chat_id,
                      document=gif, caption=f'Bom dia, *{chove}* em {location} hoje '
                                            f'*({chance_of_rain}% at {time_of_rain})*.'
                                            f'\nMax Temp: *{max_temp}*C', timeout=5000,
                      parse_mode=telegram.ParseMode.MARKDOWN)


def scheduled_weather(bot, job):
    locations = ['london', 'Maisons-Laffitte', 'Barcelona', 'Geneva']
    for l in locations:
        results = get_weather(l)
        max_temp = results['daily']['data'][0]['temperatureMax']
        chove, time_of_rain, chance_of_rain = vai_chover(l)
        logger.info(f'Chove? {chove}')
        if chove == 'Vai chover':
            gif = get_random_giphy(keyword='sad')
        else:
            gif = get_random_giphy(keyword='happy')
        bot.send_document(chat_id=-1001105653255,
                          document=gif, caption=f'Bom dia!\n'
                                                f'*{chove}* hoje em {l} *({chance_of_rain}% at {time_of_rain})*.'
                                                f'\nMax Temp: *{max_temp}*C', timeout=5000,
                          parse_mode=telegram.ParseMode.MARKDOWN)


def send_weather(bot, update, location=None):
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
    # highest_chance_of_rain = 0
    # day_summary = {}
    # for i in results['hourly']['data']:
    #     if i['precipProbability'] > 0 and i['precipProbability'] > highest_chance_of_rain:
    #         highest_chance_of_rain = i['precipProbability']
    #         day_summary = {'chance': highest_chance_of_rain * 100,
    #                        'time': i['time'], 'summary': i['summary']}
    chance_of_rain, time_of_rain = chance_of_rain_today(results)
    next_hour = results.get('minutely')
    if next_hour:
        minutely = next_hour.get('summary')
    else:
        minutely = '-'


    message = f'''Good Morning {update.message.chat.title}, here is your daily forecast for {location}:

    *Current Conditions:*
    {results['currently']['summary']}
    Chance of Rain: {results['currently']['precipProbability'] * 100}%, Current Temperature: {results['currently']['temperature']}C

    *Summary of conditions for the next hour:*
    {results['minutely']['summary']}

    *Conditions for the rest of the day:*
    {results['hourly']['summary']}
    Highest Chance of Rain: {chance_of_rain}% at {time_of_rain}

    *Summary of conditions for the rest of the week:*
    {results['daily']['summary']}
    {minutely}'''

    bot.send_message(chat_id=update.message.chat_id,
                     text=f'*Monolognator Weather Report powered by darksky.net*:\n\n{message}',
                     parse_mode=telegram.ParseMode.MARKDOWN)
