
import telegram
import random
import logging
import re

from gif import send_random_tenor

logger = logging.getLogger(__name__)


counter = {}
msg_limit = {}
my_chat_id = 113426151

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
        # bot.send_message(chat_id=my_chat_id,
        #                  text=f'Manual limit set on {update.message.chat.title}'
        #                       f' by {update.message.from_user.first_name}: {msg_limit[update.message.chat_id]}')


# MONOLOGNATE STUFF
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
                         "\n".join(counter[chat][user]['msgs'])),
                     parse_mode=telegram.ParseMode.MARKDOWN,
                     timeout=15)
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

