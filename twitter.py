import tweepy
import json
import queue
import logging
import time
logger = logging.getLogger(__name__)


tqueue = queue.Queue()


class Stream(tweepy.StreamListener):
    def __init__(self, api):
        self.api = api
        self.me = api.me()

    def on_connect(self):
        # Called initially to connect to the Streaming API
        print("Connected streaming API.")

    def on_limit(self, track):
        print(f'Limit message received: {track}, Sleeping for 60 seconds')
        time.sleep(60)

    # TODO fix multiple ifs into single one
    def on_status(self, tweet):
        print('On Status Triggered')
        if not tweet.retweeted:
            if 'RT @' not in tweet.text:
                if not tweet.is_quote_status:
                    if not tweet.in_reply_to_status_id:
                        logger.debug(f'{tweet.user.screen_name}, {tweet.retweeted}, {tweet.is_quote_status}, {tweet.in_reply_to_status_id}')
                        tqueue.put(tweet)

    def on_error(self, status):
        print(f"Error detected {status}")
        if status == 420:
            #returning False in on_error disconnects the stream
            return False



