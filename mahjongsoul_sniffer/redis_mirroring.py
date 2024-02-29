#!/usr/bin/env python3
# ruff: noqa: S101, RUF003

import base64
import datetime
import json
import logging
import re

import jsonschema
import wsproto.frame_protocol
from mitmproxy.websocket import WebSocketData

import mahjongsoul_sniffer.redis as redis_
from mahjongsoul_sniffer import mahjongsoul_pb2

_NOP_ACTION_CONFIG_SCHEMA = {
    "const": "NOP",
}


_LPUSH_ACTION_CONFIG_SCHEMA = {
    "type": "object",
    "required": [
        "command",
        "key",
    ],
    "properties": {
        "command": {
            "const": "LPUSH",
        },
        "key": {
            "type": "string",
        },
    },
    "additionalProperties": False,
}


_LPUSHX_ACTION_CONFIG_SCHEMA = {
    "type": "object",
    "required": [
        "command",
        "key",
    ],
    "properties": {
        "command": {
            "const": "LPUSHX",
        },
        "key": {
            "type": "string",
        },
    },
    "additionalProperties": False,
}


_RPUSH_ACTION_CONFIG_SCHEMA = {
    "type": "object",
    "required": [
        "command",
        "key",
    ],
    "properties": {
        "command": {
            "const": "RPUSH",
        },
        "key": {
            "type": "string",
        },
    },
    "additionalProperties": False,
}


_RPUSHX_ACTION_CONFIG_SCHEMA = {
    "type": "object",
    "required": [
        "command",
        "key",
    ],
    "properties": {
        "command": {
            "const": "RPUSHX",
        },
        "key": {
            "type": "string",
        },
    },
    "additionalProperties": False,
}


_SET_ACTION_CONFIG_SCHEMA = {
    "type": "object",
    "required": [
        "command",
        "key",
    ],
    "properties": {
        "command": {
            "const": "SET",
        },
        "key": {
            "type": "string",
        },
        "ex": {
            "type": "integer",
        },
        "px": {
            "type": "integer",
        },
        "nx": {
            "type": "boolean",
        },
        "xx": {
            "type": "boolean",
        },
    },
    "additionalProperties": False,
}


_ACTION_CONFIG_SCHEMA = {
    "oneOf": [
        _NOP_ACTION_CONFIG_SCHEMA,
        _LPUSH_ACTION_CONFIG_SCHEMA,
        _LPUSHX_ACTION_CONFIG_SCHEMA,
        _RPUSH_ACTION_CONFIG_SCHEMA,
        _RPUSHX_ACTION_CONFIG_SCHEMA,
        _SET_ACTION_CONFIG_SCHEMA,
    ],
}


_HTTP_CONFIG_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": [
            "url_pattern",
            "action",
        ],
        "properties": {
            "url_pattern": {
                "type": "string",
            },
            "action": _ACTION_CONFIG_SCHEMA,
        },
        "additionalProperties": False,
    },
}


_WEBSOCKET_MESSAGE_CONFIG_SCHEMA = {
    "type": "object",
    "required": [
        "request_direction",
        "action",
    ],
    "properties": {
        "request_direction": {
            "enum": [
                "inbound",
                "outbound",
                "both",
            ],
        },
        "action": _ACTION_CONFIG_SCHEMA,
    },
    "additionalProperties": False,
}


_METHOD_NAMES = [
    "." + mdesc.full_name
    for sdesc in mahjongsoul_pb2.DESCRIPTOR.services_by_name.values()
    for mdesc in sdesc.methods
]


_MESSAGE_TYPE_NAMES = [
    "." + tdesc.full_name
    for tdesc in mahjongsoul_pb2.DESCRIPTOR.message_types_by_name.values()
]


_WEBSOCKET_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}
for mname in _METHOD_NAMES:
    _WEBSOCKET_CONFIG_SCHEMA["properties"][
        mname
    ] = _WEBSOCKET_MESSAGE_CONFIG_SCHEMA
for tname in _MESSAGE_TYPE_NAMES:
    _WEBSOCKET_CONFIG_SCHEMA["properties"][
        tname
    ] = _WEBSOCKET_MESSAGE_CONFIG_SCHEMA


_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "http": _HTTP_CONFIG_SCHEMA,
        "websocket": _WEBSOCKET_CONFIG_SCHEMA,
    },
    "additionalProperties": False,
}


def _execute_action(data: dict, action: dict, r: redis_.Redis) -> None:  # noqa: C901
    if isinstance(action, str) and action == "NOP":
        return

    command = action["command"]
    key = action["key"]
    dumped_data = json.dumps(data, allow_nan=False, separators=(",", ":"))
    encoded_data = dumped_data.encode("UTF-8")

    if command == "LPUSH":
        r.lpush(key, encoded_data)
    elif command == "LPUSHX":
        r.lpushx(key, encoded_data)
    elif command == "RPUSH":
        r.rpush(key, encoded_data)
    elif command == "RPUSHX":
        r.rpushx(key, encoded_data)
    elif command == "SET":
        options = {}
        if "ex" in action:
            options["ex"] = action["ex"]
        if "px" in action:
            options["px"] = action["px"]
        if "nx" in action:
            options["nx"] = action["nx"]
        if "xx" in action:
            options["xx"] = action["xx"]
        r.set(key, encoded_data, **options)


class RedisMirroring:
    def __init__(self, *, module_name: str, config: dict) -> None:
        self.__redis = redis_.Redis(module_name=module_name)
        jsonschema.validate(instance=config, schema=_CONFIG_SCHEMA)
        self.__config = config
        self.__websocket_message_queue: dict = {}

    def on_websocket_message(self, websocket_data: WebSocketData) -> None:  # noqa: C901
        if len(websocket_data.messages) == 0:
            msg = "`len(websocket_data.messages)` == 0"
            raise RuntimeError(msg)
        message = websocket_data.messages[-1]

        if message.type != wsproto.frame_protocol.Opcode.BINARY:
            msg = f"{message.type}: An unsupported WebSocket message type."
            raise RuntimeError(msg)

        direction = "outbound" if message.from_client else "inbound"

        content = message.content

        m = re.search(
            b"^(?:\x01|\x02..)\n.(.*?)\x12",
            content,
            flags=re.DOTALL,
        )
        if m is not None:
            type_ = content[0]
            assert type_ in [1, 2]

            number = None
            if type_ == 2:
                number = int.from_bytes(content[1:3], byteorder="little")

            name = m.group(1).decode("UTF-8")

            if type_ == 2:
                # レスポンスメッセージを期待するリクエストメッセージの処理．
                # 対応するレスポンスメッセージが検出されるまでメッセージを
                # キューに保存しておく．
                if number in self.__websocket_message_queue:
                    prev_request = self.__websocket_message_queue[number]
                    logging.warning(
                        """There is not any response message\
 for the following WebSocket request message:
direction: %s
content: %s""",
                        prev_request["direction"],
                        prev_request["request"],
                    )

                self.__websocket_message_queue[number] = {
                    "direction": direction,
                    "name": name,
                    "request": content,
                }

                return

            # レスポンスを必要としないリクエストメッセージの処理．
            assert type_ == 1
            assert number is None

            request_direction = direction
            request = content

            if request_direction == "outbound":
                direction = "inbound"
            else:
                assert request_direction == "inbound"
                direction = "outbound"
            response = None
        else:
            # レスポンスメッセージ．
            # キューから対応するリクエストメッセージを探し出す．
            m = re.search(b"^\x03..\n\x00\x12", content, flags=re.DOTALL)
            if m is None:
                msg = f"""An unknown WebSocket message:
direction: {direction}
content: {content!r}"""
                raise RuntimeError(msg)

            number = int.from_bytes(content[1:3], byteorder="little")
            if number not in self.__websocket_message_queue:
                msg = f"""An WebSocket response message\
 that does not match to any request message:
direction: {direction}
content: {content!r}"""
                raise RuntimeError(msg)

            request_direction = self.__websocket_message_queue[number][
                "direction"
            ]
            name = self.__websocket_message_queue[number]["name"]
            request = self.__websocket_message_queue[number]["request"]
            response = content
            del self.__websocket_message_queue[number]

        if request_direction == "inbound":
            if direction == "inbound":
                msg = "Both request and response WebSocket\
 messages are inbound."
                raise RuntimeError(msg)
            assert direction == "outbound"
        else:
            assert request_direction == "outbound"
            if direction == "outbound":
                msg = "Both request and response WebSocket\
 messages are outbound."
                raise RuntimeError(msg)
            assert direction == "inbound"

        match = True
        while True:
            if "websocket" not in self.__config:
                match = False
                break
            websocket_config = self.__config["websocket"]
            if name not in websocket_config:
                match = False
                break
            expected_request_direction = websocket_config[name][
                "request_direction"
            ]
            if expected_request_direction not in [request_direction, "both"]:
                match = False
                break
            break

        if match:
            decoded_request = base64.b64encode(request).decode("UTF-8")
            if response is not None:
                decoded_response = base64.b64encode(response).decode("UTF-8")
            else:
                decoded_response = None
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            data = {
                "request_direction": request_direction,
                "request": decoded_request,
                "response": decoded_response,
                "timestamp": now.timestamp(),
            }
            _execute_action(
                data,
                self.__config["websocket"][name]["action"],
                self.__redis,
            )
            return

        logging.warning(
            """An unhandled WebSocket message:
request_direction: %s
request: %s
response: %s""",
            request_direction,
            request,
            response,
        )
