#!/usr/bin/env python3

import logging
from mitmproxy.websocket import WebSocketMessage


def on_oauth2_login(request_message: WebSocketMessage,
                    response_message: WebSocketMessage) -> None:
    logging.info("Skip WebSocket messages from/to `.lq.Lobby.oauth2Login'.")
