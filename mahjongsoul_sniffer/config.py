#!/usr/bin/env python3

import pathlib
import logging
import logging.handlers
import yaml
import jsonschema
from mahjongsoul_sniffer.redis_log_handler import RedisLogHandler


_REDIS_CONFIG_SCHEMA = {
    'type': 'object',
    'required': [
        'host'
    ],
    'properties': {
        'host': {
            'type': 'string'
        },
        'port': {
            'oneOf': [
                {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 65535
                },
                {
                    'const': None
                }
            ]
        }
    },
    'additionalProperties': False
}


_S3_CONFIG_SCHEMA = {
    'type': 'object',
    'required': [
        'bucket'
    ],
    'properties': {
        'bucket': {
            'type': 'string'
        },
        'key_prefix': {
            'oneOf': [
                {
                    'type': 'string'
                },
                {
                    'const': None
                }
            ]
        }
    },
    'additionalProperties': False
}


_GOOGLE_API_CONFIG_SCHEMA = {
    'type': 'object',
    'properties': {
        'token_path': {
            'oneOf': [
                {
                    'type': 'string'
                },
                {
                    'const': None
                }
            ]
        }
    },
    'additionalProperties': False
}


_LOGGING_CONFIG_SCHEMA = {
    'type': 'object',
    'properties': {
        'level': {
            'enum': [
                'DEBUG',
                'INFO',
                'WARNING',
                'ERROR',
                'CRITICAL',
                None
            ]
        },
        'max_entries': {
            'oneOf': [
                {
                    'type': 'integer',
                    'minimum': 0
                },
                {
                    'const': None
                }
            ]
        }
    },
    'additionalProperties': False
}


_CONFIG_SCHEMA = {
    'type': 'object',
    'required': [
        'redis',
        's3',
    ],
    'properties': {
        'redis': _REDIS_CONFIG_SCHEMA,
        's3': _S3_CONFIG_SCHEMA,
        'google_api': _GOOGLE_API_CONFIG_SCHEMA,
        'sniffer': {
            'type': 'object',
            'properties': {
                'logging': _LOGGING_CONFIG_SCHEMA
            },
            'additionalProperties': False
        },
        'game_abstract_archiver': {
            'type': 'object',
            'properties': {
                'logging': _LOGGING_CONFIG_SCHEMA
            },
            'additionalProperties': False
        },
        'game_abstract_crawler': {
            'type': 'object',
            'properties': {
                'logging': _LOGGING_CONFIG_SCHEMA
            },
            'additionalProperties': False
        }
    },
    'additionalProperties': False
}


_CONFIG_PATH = pathlib.Path('config.yaml')


if not _CONFIG_PATH.exists():
    raise RuntimeError(f'{_CONFIG_PATH}: File does not exist.')
if not _CONFIG_PATH.is_file():
    raise RuntimeError(f'{_CONFIG_PATH}: Not a file.')
with open(_CONFIG_PATH) as config_file:
    _CONFIG = yaml.load(config_file, Loader=yaml.Loader)
jsonschema.validate(instance=_CONFIG, schema=_CONFIG_SCHEMA)


def initialize_logging(name: str) -> None:
    default_logging_config = {
        'level': 'INFO',
        'max_entries': 100
    }

    if name == 'sniffer':
        log_key = 'log.sniffer'
        if 'sniffer' in _CONFIG and 'logging' in _CONFIG['sniffer']:
            logging_config = _CONFIG['sniffer']['logging']
        else:
            logging_config = default_logging_config
    elif name == 'game abstract archiver':
        log_key = 'log.archiver'
        if 'game_abstract_archiver' in _CONFIG \
           and 'logging' in _CONFIG['game_abstract_archiver']:
            logging_config = _CONFIG['game_abstract_archiver']['logging']
        else:
            logging_config = default_logging_config
    elif name == 'game abstract crawler':
        log_key = 'log.crawler'
        if 'game_abstract_crawler' in _CONFIG \
           and 'logging' in _CONFIG['game_abstract_crawler']:
            logging_config = _CONFIG['game_abstract_crawler']['logging']
        else:
            logging_config = default_logging_config
    else:
        raise ValueError(f'name == {name}')

    if 'level' not in logging_config or logging_config['level'] is None:
        logging_config['level'] = logging.INFO
    elif logging_config['level'] == 'DEBUG':
        logging_config['level'] = logging.DEBUG
    elif logging_config['level'] == 'INFO':
        logging_config['level'] = logging.INFO
    elif logging_config['level'] == 'WARNING':
        logging_config['level'] = logging.WARNING
    elif logging_config['level'] == 'ERROR':
        logging_config['level'] = logging.ERROR
    elif logging_config['level'] == 'CRITICAL':
        logging_config['level'] = logging.CRITICAL
    else:
        raise ValueError(f'level == {logging_config["level"]}')

    if 'max_entries' not in logging_config \
       or logging_config['max_entries'] is None:
        logging_config['max_entries'] = 0

    redis_config = _CONFIG['redis']
    redis_host = redis_config['host']
    if 'port' not in redis_config or redis_config['port'] is None:
        redis_port = 6379
    else:
        redis_port = redis_config['port']

    log_format = '%(asctime)s:%(filename)s:%(funcName)s:%(lineno)d:\
%(levelname)s: %(message)s'
    log_handler = RedisLogHandler(
        host=redis_host, port=redis_port, key=log_key,
        max_entries=logging_config['max_entries'])
    logging.basicConfig(
        format=log_format, level=logging_config['level'],
        handlers=[log_handler])


def get_redis():
    import redis

    redis_config = _CONFIG['redis']
    redis_host = redis_config['host']
    if 'port' not in redis_config or redis_config['port'] is None:
        redis_port = 6379
    else:
        redis_port = redis_config['port']
    return redis.Redis(host=redis_host, port=redis_port)


def get_s3_bucket():
    import boto3

    s3 = boto3.resource('s3')
    return s3.Bucket(_CONFIG['s3']['bucket'])


def get_s3_key_prefix():
    if 'key_prefix' not in _CONFIG['s3'] \
       or _CONFIG['s3']['key_prefix'] is None:
        return '%k/%Y/%m/%d'
    return _CONFIG['s3']['key_prefix']


def get_gmail_api():
    import pickle
    import googleapiclient.discovery

    default_token_path = pathlib.Path('google-api-token.pickle')
    if 'google_api' not in _CONFIG \
       or 'token_path' not in _CONFIG['google_api'] \
       or _CONFIG['google_api']['token_path'] is None:
        token_path = default_token_path
    else:
        token_path = pathlib.Path(_CONFIG['google_api']['token_path'])

    if not token_path.exists():
        raise RuntimeError(f'{token_path}: File does not exist.')
    if not token_path.is_file():
        raise RuntimeError(f'{token_path}: Not a file.')
    with open(token_path, 'rb') as token:
        creds = pickle.load(token)

    return googleapiclient.discovery.build('gmail', 'v1',
                                           credentials=creds)
