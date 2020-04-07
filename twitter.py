import tweepy
import queue
import logging
import time
import yaml
import re
import string
import config
from urllib3.exceptions import ProtocolError, IncompleteRead

logger = logging.getLogger(__name__)
cfg = config.cfg()
group_id = cfg.get('group_id')
my_chat_id = cfg.get('my_chat_id')
tqueue = queue.Queue()

with open('filters.yml') as f:
    twitter_filters = yaml.load(f, Loader=yaml.FullLoader)['users']


class Stream(tweepy.StreamListener):
    def __init__(self, api):
        self.api = api
        self.me = api.me()

    def on_connect(self):
        # Called initially to connect to the Streaming API
        logger.info("Connected streaming API.")

    def on_limit(self, track):
        logger.warning(f'Limit message received: {track}, Sleeping for 60 seconds')
        time.sleep(60)

    # TODO fix multiple ifs into single one
    def on_status(self, tweet):
        # Log ping msgs every 5 minutes to check if it's working
        if time.localtime().tm_min % 5 == 0:
            logger.info(f'on_status Triggered: {tweet.user.screen_name}')
        if tweet.user.id in twitter_filters:
            logger.info(f'Tweet from {tweet.user.screen_name}.')
            if not tweet.retweeted:
                if 'RT @' not in tweet.text:
                    if not tweet.is_quote_status:
                        if not tweet.in_reply_to_status_id:
                            logger.debug(f'TWEET: {tweet.user.screen_name}, {tweet.retweeted}, {tweet.is_quote_status}, {tweet.in_reply_to_status_id}')
                            logger.info(f'Adding tweet from {tweet.user.screen_name} to queue')
                            if filter_tweet(tweet):
                                tqueue.put(tweet)
                            logger.debug(f'Queue size: {tqueue.qsize()} ')

    def on_error(self, status):
        logger.error(f"Error detected {status}")
        if status == 420:
            #returning False in on_error disconnects the stream
            return False


def filter_tweet(tweet):
    user_id = tweet.user.id
    name = tweet.user.screen_name
    text = tweet.text
    logger.debug(f'Filtering Tweet from {name}: {text}')
    if user_id in twitter_filters:
        logger.info(f'Tweet: https://twitter.com/{name}/status/{tweet.id}')
        logger.debug(f'Tweet from {name} is in filters: {text} ')
        user = twitter_filters.get(tweet.user.id)
        user_filter = user.get('filter')
        filter_type = user.get('type')
        text = text.lower()
        new_text = re.sub(r'http\S+', '', text)
        regex = re.compile('[%s]' % re.escape(string.punctuation))
        new_text = regex.sub('', new_text).lower()
        text_list = new_text.split()
        if user_filter:
            # logger.info(f'Tweet from: {name}')
            # logger.info(f'Filter: {user_filter}, Words: {text_list}')
            if filter_type == 'string':
                if any(word.lower() in text_list for word in user_filter):
                    logger.info(f'MATCH {name},filter: {user_filter}')
                    logger.info(f'Words: {text_list}')
                    # return f'https://twitter.com/{name}/status/{tweet.id}'
                    return True
                else:
                    logger.info(f'NO MATCH. filter: {user_filter}, words: {text_list}')
                    return False
            if filter_type == 'regex':
                rex = re.compile(user_filter)
                if rex.findall(text, re.IGNORECASE):
                    logger.info(f'Filter match for {name}, type:{filter_type}')
                    logger.info(f'Word: {text_list}')
                    # return f'https://twitter.com/{name}/status/{tweet.id}'
                    return True
                else:
                    return False
        logger.info(f'User match for {name}, empty filter')
        # return f'https://twitter.com/{name}/status/{tweet.id}'
        return True
    # logger.info(f'Dropping tweet from {name}, {user_id}, {text}, ')
    return False


def start_twitter_stream():
    auth = tweepy.OAuthHandler(cfg.get('twitter_api_key'),
                               cfg.get('twitter_api_secret'))
    auth.set_access_token(cfg.get('twitter_token'),
                          cfg.get('twitter_token_secret'))

    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    tweets_listener = Stream(api)
    try:
        logger.info('Starting Stream filter')
        stream = tweepy.Stream(api.auth, tweets_listener)
        stream.filter(follow=[str(a) for a in twitter_filters.keys()], is_async=True)
    except tweepy.TweepError as e:
        stream.disconnect()
        logger.error(f"TweepyError exception: {e}")
        start_twitter_stream()
    except (ProtocolError, AttributeError, IncompleteRead) as e:
        stream.disconnect()
        logger.error(f"TweepyError exception: {e}")
        start_twitter_stream()
    except Exception:
        stream.disconnect()
        logger.error("Fatal exception. Consult logs.")
        start_twitter_stream()


def send_tweets(bot, update):
    logger.debug('Checking queue')
    logger.debug(f'Queue sized when reading: {tqueue.qsize()}')
    while not tqueue.empty():
        tweet = tqueue.get()
        url = f'https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}'
        if url:
            logger.info(f'Sending tweet from {tweet.user.screen_name}')
            bot.send_message(chat_id=group_id, text=url)

