#!/usr/bin/env python3

import logging
from mitmproxy.websocket import WebSocketMessage
from mahjongsoul_sniffer.sniffer.websocket.mahjongsoul_pb2 \
    import (FetchGameRecordListRequest, FetchGameRecordListResponse)


def on_fetch_game_record_list(request_message: WebSocketMessage,
                              response_message: WebSocketMessage) -> None:
    logging.info("Sniffering WebSocket message from/to"
                 " `.lq.Lobby.fetchGameRecordList'.")

    request_string = request_message.content
    request = FetchGameRecordListRequest()
    request.ParseFromString(request_string[36:])
    print(request)

    response_string = response_message.content
    response = FetchGameRecordListResponse()
    response.ParseFromString(response_string[8:])
    print(response)
