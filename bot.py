from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import telegram
import random
import logging
import os
import re

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

counter = {}
previous_user = None
msg_limit = random.randint(5, 12)
print(f'First msg limit: {msg_limit}')


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="I'm The MonologNator. I'll be back")


def limit(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text=f"Current random monologue limit: {msg_limit}")


def set_limit(bot, update):
    print(update.message.text)
    global msg_limit
    msg = update.message.text
    msg_limit = int(re.findall('[0-9]+', msg)[0])

    logger.info(f'New Limit set by {update.message.from_user.first_name}: {msg_limit}')


def count(bot, update):
    global counter
    global previous_user
    global msg_limit

    user = update.message.from_user.id

    # Check if counter exists, if not. start it
    if user not in counter:
        counter[user] = {}
        counter[user]['count'] = 1
        counter[user]['msg_ids'] = list()
        counter[user]['msg_ids'].append(update.message.message_id)
        counter[user]['msgs'] = list()
        counter[user]['msgs'].append(update.message.text)
    else:
        # if current msg is by the same user as previous msg, increase counter
        if user == previous_user:
            counter[user]['count'] += 1
            counter[user]['msg_ids'].append(update.message.message_id)
            counter[user]['msgs'].append(update.message.text)
        else:
            # otherwise, reset counter for previous user
            print(f'Reseting the counter for {previous_user}')
            counter[previous_user]['count'] = 1
            counter[previous_user]['msg_ids'] = list()
            counter[previous_user]['msgs'] = list()

    print(f'Count for {user}: {counter[user]["count"]}')
    previous_user = user
    # print(update.message)
    print(f'limit: {msg_limit}')
    print(counter[user]['msg_ids'])
    print(counter[user]['msgs'])

    # of count for user = 5, send alert
    # if counter[user]['count'] == 5:
    #     bot.send_message(chat_id=113426151, text=f'New msg limit set: {msg_limit}')
    #     print(f'{user} hit the warning counter')
        # bot.send_message(chat_id=update.message.chat_id,
        #                 text=f'Hold your horses {update.message.from_user.first_name},'
        #                       f' that was a {counter[user]["count"]} line monologue!!!!\n'
        #                       f'The next time, I will terminate your monologue!')

        # If count = 10, delete previous msgs and send summary
    user_count = counter[user]['count']
    if user_count == msg_limit:
        # Clear counter for user

        counter[user]['count'] = 0
        # Reset randon limit
        msg_limit = random.randint(5, 12)
        print(f'New random limit: {msg_limit}')
        bot.send_message(chat_id=113426151, text=f'New msg limit set: {msg_limit}')

        print(f'{user} hit the fuck face counter')
        #bot.send_message(chat_id=update.message.chat_id,
        #                 text=f'I told you, fuck face! Im terminating your monologue,'
        #                      f' {update.message.from_user.first_name}')
        for m in set(counter[user]['msg_ids']):
            bot.delete_message(chat_id=update.message.chat_id, message_id=m)

        # Send message with the last 10 message by the user
        bot.send_document(chat_id=update.message.chat_id, document=open('./tsunami.gif', 'rb'), timeout=100)
        bot.send_message(chat_id=update.message.chat_id,
                         text='*Monologue by {}*:\n\n`{}`'.format(
                             update.message.from_user.first_name,
                             "\n".join(counter[user]['msgs'])), parse_mode=telegram.ParseMode.MARKDOWN)

        counter[user]['msgs'] = list()
        counter[user]['msg_ids'] = list()




updater = Updater(os.getenv('telegram_token'))
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('limit', limit))
updater.dispatcher.add_handler(CommandHandler('set_limit', set_limit))


updater.dispatcher.add_handler(MessageHandler(Filters.text, count))
updater.start_polling()
updater.idle()
