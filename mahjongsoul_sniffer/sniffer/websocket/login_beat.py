#!/usr/bin/env python3

import datetime
import logging
from mitmproxy.websocket import WebSocketMessage
import mahjongsoul_sniffer.config


def on_login_beat(request_message: WebSocketMessage,
                  response_message: WebSocketMessage) -> None:
    logging.info(
        "Sniffering WebSocket messages from/to `.lq.Lobby.loginBeat'.")

    r = mahjongsoul_sniffer.config.get_redis()
    timestamp = int(
        datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
    r.hset('api-timestamp', 'loginBeat', timestamp)
