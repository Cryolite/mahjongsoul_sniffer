#!/usr/bin/env python3

import datetime
import json
import base64
from typing import (Optional, List)
import jsonschema
import mahjongsoul_sniffer.config


_WEBSOCKET_MESSAGE_SCHEMA = {
    'type': 'object',
    'requiredProperties': [
        'request_direction',
        'request',
        'response',
        'timestamp'
    ],
    'properties': {
        'request_direction': {
            'enum': [
                'inbound',
                'outbound'
            ]
        },
        'request': {
            'type': 'string'
        },
        'response': {
            'type': 'string'
        },
        'timestamp': {
            'type': 'number'
        }
    },
    'additionalProperties': False
}


class RedisClient(object):
    def __init__(self):
        self.__redis = mahjongsoul_sniffer.config.get_redis()

    def __decode_websocket_message(self, message: bytes) -> dict:
        message = message.decode('UTF-8')
        message = json.loads(message)
        jsonschema.validate(instance=message,
                            schema=_WEBSOCKET_MESSAGE_SCHEMA)

        message['request'] = base64.b64decode(message['request'])
        message['response'] = base64.b64decode(message['response'])
        message['timestamp'] = datetime.datetime.fromtimestamp(
            message['timestamp'], tz=datetime.timezone.utc)

        return message

    def get_websocket_message(self, key: str) -> Optional[dict]:
        message = self.__redis.get(key)
        if message is None:
            return None
        return self.__decode_websocket_message(message)

    def blpop_websocket_message(self, key: str) -> dict:
        message = self.__redis.blpop(key)
        assert(message[0].decode('UTF-8') == key)
        return self.__decode_websocket_message(message[1])

    def set_timestamp(self, key: str) -> None:
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        self.__redis.set(key, str(now.timestamp()).encode('UTF-8'))

    def get_timestamp(self, key: str) -> Optional[datetime.datetime]:
        timestamp = self.__redis.get(key)

        if timestamp is None:
            return None

        timestamp = timestamp.decode('UTF-8')
        timestamp = float(timestamp)
        timestamp = datetime.datetime.fromtimestamp(
            timestamp, tz=datetime.timezone.utc)
        return timestamp

    def get_all_log_records(self, key: str) -> List[str]:
        key = key.encode('UTF-8')
        records = self.__redis.lrange(key, 0, -1)
        records = [record.decode('UTF-8') for record in records]
        return records
