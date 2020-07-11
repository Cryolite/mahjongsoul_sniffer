#!/usr/bin/env python3

import pathlib
import logging
from mitmproxy.websocket import WebSocketMessage


def on_login_beat(request_message: WebSocketMessage,
                  response_message: WebSocketMessage) -> None:
    logging.info(
        "Sniffering WebSocket messages from/to `.lq.Lobby.loginBeat'.")

    if not pathlib.Path('output').exists():
        raise RuntimeError('`output` does not exist.')
    if not pathlib.Path('output').is_dir():
        raise RuntimeError('`output` is not a directory.')

    pathlib.Path('output/login.timestamp').touch()
