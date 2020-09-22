#!/usr/bin/env python3

import logging
import redis


class RedisLogHandler(logging.Handler):
    def __init__(self, host: str, port: int, key: str,
                 max_entries: int=0):
        if max_entries < 0:
            raise ValueError(f'`max_entries == {max_entries}`')

        super().__init__()
        self.__key = key.encode('UTF-8')
        self.__max_entries = max_entries
        self.__redis = redis.Redis(host=host, port=port)

    def emit(self, record: logging.LogRecord) -> None:
        message = super().format(record)
        message = message.encode('UTF-8')
        self.__redis.rpush(self.__key, message)

        if self.__max_entries == 0:
            return

        while True:
            length = self.__redis.llen(self.__key)
            if length <= self.__max_entries:
                break
            self.__redis.lpop(self.__key)
