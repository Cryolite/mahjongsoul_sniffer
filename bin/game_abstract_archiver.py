#!/usr/bin/env python3

import re
import datetime
import pathlib
import logging
import logging.handlers
import json
import typing
import yaml
import jsonschema
import redis
import boto3


_config_schema = {
    'type': 'object',
    'required': [
        'logging',
        'redis'
    ],
    'properties': {
        'logging': {
            'type': 'object',
            'required': [
                'log_file'
            ],
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
                'log_file': {
                    'type': 'object',
                    'required': [
                        'path'
                    ],
                    'properties': {
                        'path': {
                            'type': 'string'
                        },
                        'max_bytes': {
                            'oneOf': [
                                {
                                    'type': 'integer',
                                    'minimum': 0
                                },
                                {
                                    'const': None
                                }
                            ]
                        },
                        'backup_count': {
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
            },
            'additionalProperties': False
        },
        'redis': {
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
        },
        'local': {
            'type': 'object',
            'required': [
                'prefix'
            ],
            'properties': {
                'prefix': {
                    'type': 'string'
                }
            },
            'additionalProperties': False
        },
        's3': {
            'type': 'object',
            'required': [
                'bucket',
                'key_prefix'
            ],
            'properties': {
                'bucket': {
                    'type': 'string'
                },
                'key_prefix': {
                    'type': 'string'
                }
            },
            'additionalProperties': False
        }
    },
    'additionalProperties': False
}


class _Config(object):
    def __init__(self):
        config_file_path = pathlib.Path('config/game_abstract_archiver.yaml')
        if not config_file_path.exists():
            raise RuntimeError(
                f"Config file `{config_file_path}' does not exist.")
        if not config_file_path.is_file():
            raise RuntimeError(f"`{config_file_path}' is expected to be a"
                               " config file but not a file.")

        with open(config_file_path) as config_file:
            config = yaml.load(config_file, Loader=yaml.Loader)
        jsonschema.validate(instance=config, schema=_config_schema)

        self._config = config

        log_format = '%(asctime)s:%(filename)s:%(funcName)s:%(lineno)d:\
%(levelname)s: %(message)s'

        logging_config = self._config['logging']

        if 'level' not in logging_config:
            logging_level = 'INFO'
        else:
            logging_level = logging_config['level']
            if logging_level is None:
                logging_level = 'INFO'

        log_file_config = logging_config['log_file']

        if 'max_bytes' not in log_file_config:
            log_file_max_bytes = 0
        else:
            log_file_max_bytes = log_file_config['max_bytes']
            if log_file_max_bytes is None:
                log_file_max_bytes = 0

        if 'backup_count' not in log_file_config:
            log_file_backup_count = 0
        else:
            log_file_backup_count = log_file_config['backup_count']
            if log_file_backup_count is None:
                log_file_backup_count = 0

        log_handler = logging.handlers.RotatingFileHandler(
            filename=log_file_config['path'], maxBytes=log_file_max_bytes,
            backupCount=log_file_backup_count, delay=True)
        logging.basicConfig(format=log_format, level=logging_level,
                            handlers=[log_handler])

    @property
    def logging_level(self) -> str:
        if 'level' in self._config['logging']:
            logging_level = self._config['logging']['level']
            if logging_level is None:
                logging_level = 'INFO'
        else:
            logging_level = 'INFO'
        return logging_level

    @property
    def log_file_path(self) -> pathlib.Path:
        return self._config['logging']['log_file']['path']

    @property
    def log_file_max_bytes(self) -> typing.Optional[int]:
        if 'max_bytes' in self._config['logging']['log_file']:
            log_file_max_bytes = \
                self._config['logging']['log_file']['max_bytes']
            if log_file_max_bytes == 0:
                log_file_max_bytes = None
        else:
            log_file_max_bytes = None
        return log_file_max_bytes

    @property
    def log_file_backup_count(self) -> typing.Optional[int]:
        if 'backup_count' in self._config['logging']['log_file']:
            log_file_backup_count = \
                self._config['logging']['log_file']['backup_count']
            if log_file_backup_count == 0:
                log_file_backup_count = None
        else:
            log_file_backup_count = None
        return log_file_backup_count

    @property
    def redis_host(self) -> str:
        return self._config['redis']['host']

    @property
    def redis_port(self) -> int:
        if 'port' not in self._config['redis']:
            return 6379
        if self._config['redis']['port'] is None:
            return 6379
        return self._config['redis']['port']

    @property
    def local(self) -> typing.Optional[object]:
        if 'local' not in self._config:
            return None
        return self._config['local']

    @property
    def s3(self) -> typing.Optional[object]:
        if 's3' not in self._config:
            return None
        return self._config['s3']


_config = _Config()


class LocalWriter(object):
    def __init__(self, config: object):
        self._prefix = config['prefix']

    def write(self, *, uuid: str, mode: str,
              start_time: datetime.datetime) -> None:
        prefix = start_time.strftime(self._prefix)
        prefix = pathlib.Path(prefix)
        prefix.mkdir(parents=True, exist_ok=True)

        data = {
            'uuid': uuid,
            'mode': mode,
            'start_time': int(start_time.timestamp())
        }

        with open(prefix / uuid, 'w') as f:
            json.dump(data, f, ensure_ascii=False, allow_nan=False,
                      separators=(',', ':'))


class S3Writer(object):
    def __init__(self, config: object):
        s3 = boto3.resource('s3')
        self._bucket = s3.Bucket(config['bucket'])
        self._key_prefix = config['key_prefix']

    def write(self, *, uuid: str, mode: str,
              start_time: datetime.datetime) -> None:
        key_prefix = start_time.strftime(self._key_prefix)
        key_prefix = re.sub('/+$', '', key_prefix)
        key = key_prefix + '/' + uuid

        data = {
            'uuid': uuid,
            'mode': mode,
            'start_time': int(start_time.timestamp())
        }
        data = json.dumps(data, ensure_ascii=False, allow_nan=False,
                          separators=(',', ':'))
        data = data.encode('utf-8')

        self._bucket.put_object(Key=key, Body=data)


def main():
    r = redis.Redis(host=_config.redis_host, port=_config.redis_port)

    with open('schema/game_abstract.json') as f:
        game_abstract_schema = json.load(f)

    finished = {}

    writers = []
    if _config.local is not None:
        writers.append(LocalWriter(_config.local))
    if _config.s3 is not None:
        writers.append(S3Writer(_config.s3))

    while True:
        game_abstract = r.blpop('game-abstract-list')
        game_abstract = game_abstract[1]
        game_abstract = game_abstract.decode('utf-8')
        game_abstract = json.loads(game_abstract)

        jsonschema.validate(instance=game_abstract,
                            schema=game_abstract_schema)

        uuid = game_abstract['uuid']
        if uuid in finished:
            continue

        start_time = game_abstract['start_time']
        start_time = datetime.datetime.fromtimestamp(start_time,
                                                     tz=datetime.timezone.utc)

        for writer in writers:
            writer.write(uuid=uuid, mode=game_abstract['mode'],
                         start_time=start_time)

        finished[uuid] = start_time

        if len(finished) >= 10000:
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            stale_uuid_list = []
            for uuid, start_time in finished.items():
                if now - start_time > datetime.timedelta(hours=2):
                    stale_uuid_list.append(uuid)

            for stale_uuid in stale_uuid_list:
                del finished[stale_uuid]


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.exception('An exception was thrown.')
        raise
