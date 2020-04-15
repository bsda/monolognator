from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import Filters, InlineQueryHandler, RegexHandler
from telegram.ext import CallbackQueryHandler
import logging
import datetime
import re
import config
import yaml
import gif
from twitter import start_twitter_stream, send_tweets
from updater import get_updater

cfg = config.cfg()
with open('gifs.yml') as f:
    gifs = yaml.load(f, Loader=yaml.FullLoader)

logger = logging.getLogger(__name__)

counter = {}
msg_limit = {}
group_id = cfg.get('group_id')
my_chat_id = cfg.get('my_chat_id')




def main():
    method = cfg.get('update-method') or 'polling'
    token = cfg.get('telegram_token')
    logging.basicConfig(level=cfg.get('loglevel', 'INFO'),
                        format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')

    start_twitter_stream()
    updater = get_updater()
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
