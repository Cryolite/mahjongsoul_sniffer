#!/usr/bin/env python3

import datetime
import json
import base64
from typing import (Optional, List)
import jsonschema
import redis
import mahjongsoul_sniffer.config as config_


_WEBSOCKET_MESSAGE_SCHEMA = {
    'type': 'object',
    'required': [
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
            'type': ['string', 'null']
        },
        'timestamp': {
            'type': 'number'
        }
    },
    'additionalProperties': False
}


class Redis:
    def __init__(self, *, module_name: str):
        config = config_.get(module_name)
        config = config['redis']

        host = config['host']
        port = config['port']

        self.__redis = redis.Redis(host=host, port=port)

    def set(self, key: str, value: bytes, ex=None, px=None, nx=False,
            xx=False) -> None:
        key = key.encode('UTF-8')
        self.__redis.set(key, value, ex=ex, px=px, nx=nx, xx=xx)

    def get(self, key: str) -> Optional[bytes]:
        key = key.encode('UTF-8')
        return self.__redis.get(key)

    def lpush(self, key: str, value: bytes) -> None:
        key = key.encode('UTF-8')
        self.__redis.lpush(key, value)

    def lpushx(self, key: str, value: bytes) -> None:
        key = key.encode('UTF-8')
        self.__redis.lpushx(key, value)

    def rpush(self, key: str, value: bytes) -> None:
        key = key.encode('UTF-8')
        self.__redis.rpush(key, value)

    def rpushx(self, key: str, value: bytes) -> None:
        key = key.encode('UTF-8')
        self.__redis.rpushx(key, value)

    def llen(self, key: str) -> int:
        key = key.encode('UTF-8')
        return self.__redis.llen(key)

    def lpop(self, key: str) -> Optional[bytes]:
        key = key.encode('UTF-8')
        return self.__redis.lpop(key)

    def blpop(self, key: str) -> bytes:
        key = key.encode('UTF-8')
        key_, value = self.__redis.blpop(key)
        assert(key_ == key)
        return value

    def delete(self, key: str) -> None:
        key = key.encode('UTF-8')
        self.__redis.delete(key)

    def rpush_websocket_message(self, key: str, message: dict) -> None:
        key = key.encode('UTF-8')

        message['request'] = base64.b64encode(message['request'])
        message['request'] = message['request'].decode('UTF-8')
        if message['response'] is not None:
            message['response'] = base64.b64encode(message['response'])
            message['response'] = message['response'].decode('UTF-8')
        message['timestamp'] = message['timestamp'].timestamp()
        jsonschema.validate(
            instance=message, schema=_WEBSOCKET_MESSAGE_SCHEMA)

        message = json.dumps(
            message, allow_nan=False, separators=(',', ':'))
        message = message.encode('UTF-8')

        self.__redis.rpush(key, message)

    def __decode_websocket_message(self, message: bytes) -> dict:
        message = message.decode('UTF-8')
        message = json.loads(message)
        jsonschema.validate(
            instance=message, schema=_WEBSOCKET_MESSAGE_SCHEMA)

        message['request'] = base64.b64decode(message['request'])
        if message['response'] is not None:
            message['response'] = base64.b64decode(message['response'])
        message['timestamp'] = datetime.datetime.fromtimestamp(
            message['timestamp'], tz=datetime.timezone.utc)

        return message

    def lpop_websocket_message(self, key) -> Optional[dict]:
        message = self.lpop(key)

        if message is None:
            return None

        return self.__decode_websocket_message(message)

    def blpop_websocket_message(self, key: str) -> dict:
        message = self.blpop(key)
        return self.__decode_websocket_message(message)

    def get_websocket_message(self, key: str) -> Optional[dict]:
        message = self.get(key)

        if message is None:
            return None

        return self.__decode_websocket_message(message)

    def set_timestamp(self, key: str) -> None:
        key = key.encode('UTF-8')
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        timestamp = now.timestamp()
        timestamp = str(timestamp)
        timestamp = timestamp.encode('UTF-8')
        self.__redis.set(key, timestamp)

    def get_timestamp(self, key: str) -> Optional[datetime.datetime]:
        key = key.encode('UTF-8')
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
        return [record.decode('UTF-8') for record in records]
