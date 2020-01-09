import tweepy
import json
import queue
import logging
logger = logging.getLogger(__name__)


tqueue = queue.Queue()


class Stream(tweepy.StreamListener):
    def __init__(self, api):
        self.api = api
        self.me = api.me()

    # TODO fix multiple ifs into single one
    def on_status(self, tweet):
        logger.debug('On Status Triggered')
        if not tweet.retweeted:
            if 'RT @' not in tweet.text:
                if not tweet.is_quote_status:
                    if not tweet.in_reply_to_status_id:
                        logger.debug(f'{tweet.user.screen_name}, {tweet.retweeted}, {tweet.is_quote_status}, {tweet.in_reply_to_status_id}')
                        tqueue.put(tweet)

    def on_error(self, status):
        logger.error("Error detected")



