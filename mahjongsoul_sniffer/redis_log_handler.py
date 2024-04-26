import logging

import mahjongsoul_sniffer.config as config_
import mahjongsoul_sniffer.redis as redis_


class RedisLogHandler(logging.Handler):
    def __init__(self, *, module_name: str, service_name: str) -> None:
        config = config_.get(module_name)
        config = config[service_name]
        config = config["logging"]
        config = config["redis"]

        super().__init__()

        self.__redis = redis_.Redis(module_name=module_name)
        self.__key = config["key"]
        self.__max_entries = config["max_entries"]

    def emit(self, record: logging.LogRecord) -> None:
        message = super().format(record)
        message = message.encode("UTF-8")
        self.__redis.rpush(self.__key, message)

        if self.__max_entries == 0:
            return

        while True:
            length = self.__redis.llen(self.__key)
            if length <= self.__max_entries:
                break
            self.__redis.lpop(self.__key)
