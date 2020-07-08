#!/usr/bin/env python3

import logging
from mitmproxy.websocket import WebSocketMessage


def on_fetch_collected_game_record_list(
        request_message: WebSocketMessage,
        response_message: WebSocketMessage) -> None:
    with open('collected_game_record_list.request', 'wb') as f:
        f.write(request_message.content)

    with open('collected_game_record_list.response', 'wb') as f:
        f.write(response_message.content)
