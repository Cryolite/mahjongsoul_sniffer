#!/usr/bin/env python3

import logging
from mitmproxy.websocket import WebSocketMessage


def on_fetch_shop_info(request_message: WebSocketMessage,
                       response_message: WebSocketMessage) -> None:
    logging.info("Skip WebSocket messages from/to `.lq.Lobby.fetchShopInfo'.")
