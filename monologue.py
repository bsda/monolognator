
import telegram
import random
import logging
import re
from time import sleep
from telegram.error import *

import gif
logger = logging.getLogger(__name__)


counter = {}
gif_counter = {}
msg_limit = {}
my_chat_id = 113426151


def query_limit(update, context):
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
    # context.bot.send_message(chat_id=my_chat_id,
    #                  text=f'New random limit set on {update.message.chat.title}: {msg_limit[update.message.chat_id]}')
    logger.info(f'Random limit of {msg_limit[update.message.chat_id]} set on {update.message.chat.title}')
    logger.info('================================================')
    return msg_limit[update.message.chat_id]


def set_limit(update):
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
        # context.bot.send_message(chat_id=my_chat_id,
        #                  text=f'Manual limit set on {update.message.chat.title}'
        #                       f' by {update.message.from_user.first_name}: {msg_limit[update.message.chat_id]}')


# MONOLOGNATE STUFF
def delete_messages(context, user, chat):
    # Delete messages from group
    for m in set(counter[chat][user]['msg_ids']):
        context.bot.delete_message(chat_id=chat, message_id=m)

def add_count(chat, user, update):
    global counter
    user_counter = counter[chat][user]
    user_counter['count'] += 1
    user_counter['msg_ids'].append(update.message.message_id)
    user_counter['msgs'].append(update.message.text)


def initialize_count(chat_id, user_id, user_name, chat_name, update):
    global counter
    logger.info(f'Initializing counter for {user_name} {chat_id}, {user_id}')
    logger.info(f'Count for {user_name} on {chat_name}: 1')
    # if chat not in counter:
    counter[chat_id] = {}
    counter[chat_id][user_id] = {}
    user_counter = counter[chat_id][user_id]
    user_counter['count'] = 1
    user_counter['msg_ids'] = [update.message.message_id]
    user_counter['msgs'] = [update.message.text]
    counter[chat_id]['latest_by'] = user_id


def reset_count(chat, user, update):
    global counter
    # previous_user = counter[chat]['latest_by']
    logger.info(f"Resetting the counter on {update.message.chat.title}")
    # counter[chat].pop(previous_user)
    # initialize_count(chat, user, update)
    counter[chat] = {}


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


def monolognate(chat, user, update, context):
    logger.info(f'Monologue by {update.message.from_user.first_name}')
    monologue = '\n'.join(counter[chat][user]['msgs'])
    delete_messages(context, user, chat)
    gif.send_random_tenor(update, context, 'tsunami')

    try:
        context.bot.send_message(chat_id=update.message.chat_id,
                         text='*Monólogo do {}*:\n\n`{}`'.format(
                             update.message.from_user.first_name,
                             monologue),
                         parse_mode=telegram.ParseMode.MARKDOWN,
                         timeout=15)
    except (BadRequest, RetryAfter, TimedOut, Unauthorized, NetworkError) as e:
        logger.info(f'Some Shit happened: {e}')
        logger.info(f'Trying again')
        context.bot.send_message(chat_id=update.message.chat_id,
                         text='*Monólogo do {}*:\n\n`{}`'.format(
                             update.message.from_user.first_name,
                             monologue),
                         parse_mode=telegram.ParseMode.MARKDOWN,
                         timeout=15)
    finally:
        reset_count(chat, user, update)


def handle_gifs(update, context):
    logger.info(f'{update.message.document.mime_type} received from {update.message.from_user}')
    noisy_users = ['Jgguk1', 'bsavioli']
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    if update.message.from_user.username in noisy_users:
        # delete_message(context, update.message.chat_id)
        logger.info(f'Deleting GIF from {update.message.from_user.username}')
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)

def handle_counter(update, context):
    if update.message.from_user:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name
    else:
        user_id = 'Unknown'
        user_name = 'Unknown'
    chat_id = update.message.chat_id
    if update.message.chat.type == 'private':
        chat_name = 'Private Chat'
    else:
        chat_name = update.message.chat.title
    message = update.message
    logger.info(f'Msg on {chat_name} from {user_name}: {update.message.text}')

    # If it's a new user or the count was reset earlier
    if chat_id not in counter or user_id not in counter[chat_id] and not message.reply_to_message:
        initialize_count(chat_id, user_id, user_name, chat_name, update)
    else:
        # if we seen the user before, check if previous msg was by the same user
        # if it was, increase counter and add msgs
        if user_id == counter[chat_id].get('latest_by') and not message.reply_to_message:
            add_count(chat_id, user_id, update)
            logger.info(f'Count for {user_name} on {chat_name}: {get_count(chat_id, user_id)}')
            # Check if user hit  chat limit. If it did, monolognate it
            if hit_limit(chat_id, user_id, update):
                monolognate(chat_id, user_id, update, context)
        else:
            reset_count(chat_id, user_id, update)

