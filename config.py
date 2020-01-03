
import json


def cfg():
    with open('/config/config.json') as config_file:
        data = json.load(config_file)['config']
    return data

