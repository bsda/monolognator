import requests
from datetime import datetime
import os
from bs4 import BeautifulSoup
import logging
logger = logging.getLogger(__name__)


def status():
    logger.debug('Checking corona update')
    if not os.path.exists('/tmp/corona.txt'):
        with open('/tmp/corona.txt', 'w') as file:
            old = '2000-01-01T00:00:00.000Z'
            file.write(old)

    with open('/tmp/corona.txt', 'r') as file:
        last_update = file.read().splitlines()[0]
        last_update = datetime.strptime(last_update, '%Y-%m-%dT%H:%M:%S.%fZ')

    url = 'https://www.gov.uk/api/content/guidance/wuhan-novel-coronavirus-information-for-the-public'
    res = requests.get(url).json()
    updated_at = res.get('updated_at')
    updated_at_obj = datetime.strptime(updated_at, '%Y-%m-%dT%H:%M:%S.%fZ')
    if updated_at_obj > last_update:
        logger.info('Sending Corona update')
        with open('/tmp/corona.txt', 'w') as file:
            file.write(str(updated_at))

        body = res.get('details').get('body')
        soup = BeautifulSoup(body.split('<h2')[1],  features='html.parser')
        text = soup.text.replace(' id="situation-in-the-uk">', '')
        text = f'*Latest Update:  {updated_at}*\n\n' + text

        return text
