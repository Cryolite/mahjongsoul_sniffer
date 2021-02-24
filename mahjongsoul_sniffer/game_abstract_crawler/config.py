#!/usr/bin/env python3

import pathlib
import yaml
import jsonschema


_YOSTAR_LOGIN_CONFIG_SCHEMA = {
    'type': 'object',
    'required': [
        'email_address'
    ],
    'properties': {
        'email_address': {
            'type': 'string'
        }
    },
    'additionalProperties': False
}


_REDIS_CONFIG_SCHEMA = {
    'type': 'object',
    'required': [
        'host',
        'port'
    ],
    'properties': {
        'host': {
            'type': 'string'
        },
        'port': {
            'type': 'integer',
            'minimum': 1,
            'maximum': 65535
        }
    },
    'additionalProperties': False
}


_S3_CONFIG_SCHEMA = {
    'type': 'object',
    'required': [
        'bucket_name',
        'authentication_email_key_prefix',
        'game_abstract_key_prefix'
    ],
    'properties': {
        'bucket_name': {
            'type': 'string'
        },
        'authentication_email_key_prefix': {
            'type': 'string'
        },
        'game_abstract_key_prefix': {
            'type': 'string'
        }
    },
    'additionalProperties': False
}


_LOGGING_CONFIG_SCHEMA = {
    'type': 'object',
    'required': [
        'level',
        'file',
        'redis'
    ],
    'properties': {
        'level': {
            'enum': [
                'DEBUG',
                'INFO',
                'WARNING',
                'ERROR',
                'CRITICAL'
            ]
        },
        'file': {
            'type': 'object',
            'required': [
                'path',
                'max_bytes',
                'backup_count'
            ],
            'properties': {
                'path': {
                    'type': 'string'
                },
                'max_bytes': {
                    'type': 'integer',
                    'minimum': 0
                },
                'backup_count': {
                    'type': 'integer',
                    'minimum': 0
                }
            },
            'additionalProperties': False
        },
        'redis': {
            'type': 'object',
            'required': [
                'key',
                'max_entries'
            ],
            'properties': {
                'key': {
                    'type': 'string'
                },
                'max_entries': {
                    'type': 'integer',
                    'minimum': 0
                }
            },
            'additionalProperties': False
        }
    },
    'additionalProperties': False
}


_CONFIG_SCHEMA = {
    'type': 'object',
    'required': [
        'yostar_login',
        'redis',
        's3',
        'sniffer',
        'archiver',
        'crawler'
    ],
    'properties': {
        'yostar_login': _YOSTAR_LOGIN_CONFIG_SCHEMA,
        'redis': _REDIS_CONFIG_SCHEMA,
        's3': _S3_CONFIG_SCHEMA,
        'sniffer': {
            'type': 'object',
            'required': [
                'logging'
            ],
            'properties': {
                'logging': _LOGGING_CONFIG_SCHEMA
            },
            'additionalProperties': False
        },
        'archiver': {
            'type': 'object',
            'required': [
                'logging'
            ],
            'properties': {
                'logging': _LOGGING_CONFIG_SCHEMA
            },
            'additionalProperties': False
        },
        'crawler': {
            'type': 'object',
            'required': [
                'retry_interval',
                'logging'
            ],
            'properties': {
                'retry_interval': {
                    'type': 'integer',
                    'minimum': 0
                },
                'logging': _LOGGING_CONFIG_SCHEMA
            },
            'additionalProperties': False
        }
    },
    'additionalProperties': False
}


_CONFIG_FILE_PATH = pathlib.Path('game-abstract-crawler/config.yaml')


_config = None


def get() -> dict:
    global _config

    if _config is not None:
        return _config

    if not _CONFIG_FILE_PATH.exists():
        raise RuntimeError(f'{_CONFIG_FILE_PATH}: File does not exist.')
    if not _CONFIG_FILE_PATH.is_file():
        raise RuntimeError(f'{_CONFIG_FILE_PATH}: Not a file.')

    with open(_CONFIG_FILE_PATH) as config_file:
        config = yaml.load(config_file, Loader=yaml.Loader)
    jsonschema.validate(instance=config, schema=_CONFIG_SCHEMA)

    _config = config

    return _config
