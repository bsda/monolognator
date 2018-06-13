from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import telegram
import random
import logging
import os

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

counter = {}
previous_user = None
msg_limit = random.randint(5, 12)


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="I'm The MonologNator. I'll be back")


def count(bot, update):
    global counter
    global previous_user
    global msg_limit

    user = update.message.from_user.first_name

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
    #print(update.message.text)

    # of count for user = 5, send alert
    if counter[user]['count'] == 5:
        print(f'{user} hit the warning counter')
        # bot.send_message(chat_id=update.message.chat_id,
        #                 text=f'Hold your horses {update.message.from_user.first_name},'
        #                       f' that was a {counter[user]["count"]} line monologue!!!!\n'
        #                       f'The next time, I will terminate your monologue!')

        # If count = 10, delete previous msgs and send summary
    if counter[user]['count'] == msg_limit:
        print(f'{user} hit the fuck face counter')
        #bot.send_message(chat_id=update.message.chat_id,
        #                 text=f'I told you, fuck face! Im terminating your monologue,'
        #                      f' {update.message.from_user.first_name}')
        for m in set(counter[user]['msg_ids']):
            bot.delete_message(chat_id=update.message.chat_id, message_id=m)

        # Send message with the last 10 message by the user
        bot.send_document(chat_id=update.message.chat_id, document=open('/tmp/tsunami.gif', 'rb'))
        bot.send_message(chat_id=update.message.chat_id,
                         text='*Monologue by {}*:\n\n`{}`'.format(
                             update.message.from_user.first_name,
                             "\n".join(counter[user]['msgs'])), parse_mode=telegram.ParseMode.MARKDOWN)

        # Clear counter for user
        counter[user]['msgs'] = list()
        counter[user]['msg_ids'] = list()
        counter[user]['count'] = 0
        # Reset randon limit
        msg_limit = random.randint(5, 12)
        print(f'New random limit: {msg_limit}')


updater = Updater(os.getenv('telegram_token'))
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(MessageHandler(Filters.text, count))
updater.start_polling()
updater.idle()
