from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import telegram
import random
import logging
import os
import re

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

counter = {}
previous_user = None
msg_limit = random.randint(5, 12)
my_chat_id = 113426151
logger.info(f'First msg limit: {msg_limit}')

# List of existing gifs to send to chat
gifs = ['hand', 'bla', 'incoming', 'duck', 'typing1', 'tsunami']


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="I'm The MonologNator. I'll be back")


def limit(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text=f"Current monologue limit: {msg_limit}")


def set_limit(bot, update):
    logger.info(update.message.text)
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
        # Add first msg id to counter
        counter[user]['msg_ids'].append(update.message.message_id)
        counter[user]['msgs'] = list()
        # Add first message to counter
        counter[user]['msgs'].append(update.message.text)
    else:
        # if current msg is by the same user as previous msg,
        # increase counter, add msg_id and message to counter
        if user == previous_user:
            counter[user]['count'] += 1
            counter[user]['msg_ids'].append(update.message.message_id)
            counter[user]['msgs'].append(update.message.text)
        else:
            # If it's a new user, reset counter for previous user
            logger.info(f'Reseting the counter for {previous_user}')
            counter[previous_user]['count'] = 1
            counter[previous_user]['msg_ids'] = list()
            counter[previous_user]['msgs'] = list()

    logger.info(f'Count for {user}: {counter[user]["count"]}')
    previous_user = user
    # logger.info(update.message)
    logger.info(f'limit: {msg_limit}')
    logger.info(counter[user]['msg_ids'])
    logger.info(counter[user]['msgs'])
    user_count = counter[user]['count']

    if user_count == msg_limit:
        # Clear counter for user
        counter[user]['count'] = 0

        # Reset random limit
        msg_limit = random.randint(5, 12)
        logger.info(f'New random limit: {msg_limit}')
        bot.send_message(chat_id=my_chat_id, text=f'New msg limit set: {msg_limit}')

        # Delete messages from group
        for m in set(counter[user]['msg_ids']):
            bot.delete_message(chat_id=update.message.chat_id, message_id=m)

        # Send funny gif
        bot.send_document(chat_id=update.message.chat_id,
                          document=open('./gifs/' + random.choice(gifs) + '.gif', 'rb'), timeout=100)

        # Send monologue back as a single message
        bot.send_message(chat_id=update.message.chat_id,
                         text='*Monologue by {}*:\n\n`{}`'.format(
                             update.message.from_user.first_name,
                             "\n".join(counter[user]['msgs'])), parse_mode=telegram.ParseMode.MARKDOWN)

        # reset msgs and counters for user
        counter[user]['msgs'] = list()
        counter[user]['msg_ids'] = list()


def main():

    updater = Updater(os.getenv('telegram_token'))
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('limit', limit))
    updater.dispatcher.add_handler(CommandHandler('set_limit', set_limit))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, count))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()