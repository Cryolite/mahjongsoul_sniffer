#!/usr/bin/env python3

import re
import datetime
import logging
import json
import base64
import jsonschema
import wsproto.frame_protocol
import mitmproxy.websocket
import mahjongsoul_sniffer.redis as redis_


_NOP_ACTION_CONFIG_SCHEMA = {
    'const': 'NOP'
}


_LPUSH_ACTION_CONFIG_SCHEMA = {
    'type': 'object',
    'required': [
        'command',
        'key'
    ],
    'properties': {
        'command': {
            'const': 'LPUSH'
        },
        'key': {
            'type': 'string'
        }
    },
    'additionalProperties': False
}


_LPUSHX_ACTION_CONFIG_SCHEMA = {
    'type': 'object',
    'required': [
        'command',
        'key'
    ],
    'properties': {
        'command': {
            'const': 'LPUSHX'
        },
        'key': {
            'type': 'string'
        }
    },
    'additionalProperties': False
}


_RPUSH_ACTION_CONFIG_SCHEMA = {
    'type': 'object',
    'required': [
        'command',
        'key'
    ],
    'properties': {
        'command': {
            'const': 'RPUSH'
        },
        'key': {
            'type': 'string'
        }
    },
    'additionalProperties': False
}


_RPUSHX_ACTION_CONFIG_SCHEMA = {
    'type': 'object',
    'required': [
        'command',
        'key'
    ],
    'properties': {
        'command': {
            'const': 'RPUSHX'
        },
        'key': {
            'type': 'string'
        }
    },
    'additionalProperties': False
}


_SET_ACTION_CONFIG_SCHEMA = {
    'type': 'object',
    'required': [
        'command',
        'key'
    ],
    'properties': {
        'command': {
            'const': 'SET'
        },
        'key': {
            'type': 'string'
        },
        'ex': {
            'type': 'integer'
        },
        'px': {
            'type': 'integer'
        },
        'nx': {
            'type': 'boolean'
        },
        'xx': {
            'type': 'boolean'
        }
    },
    'additionalProperties': False
}


_ACTION_CONFIG_SCHEMA = {
    'oneOf': [
        _NOP_ACTION_CONFIG_SCHEMA,
        _LPUSH_ACTION_CONFIG_SCHEMA,
        _LPUSHX_ACTION_CONFIG_SCHEMA,
        _RPUSH_ACTION_CONFIG_SCHEMA,
        _RPUSHX_ACTION_CONFIG_SCHEMA,
        _SET_ACTION_CONFIG_SCHEMA
    ]
}


_HTTP_CONFIG_SCHEMA = {
    'type': 'array',
    'items': {
        'type': 'object',
        'required': [
            'url_pattern',
            'action'
        ],
        'properties': {
            'url_pattern': {
                'type': 'string'
            },
            'action': _ACTION_CONFIG_SCHEMA
        },
        'additionalProperties': False
    }
}


_WEBSOCKET_MESSAGE_CONFIG_SCHEMA = {
    'type': 'object',
    'required': [
        'request_direction',
        'action'
    ],
    'properties': {
        'request_direction': {
            'enum': [
                'inbound',
                'outbound'
            ]
        },
        'action': _ACTION_CONFIG_SCHEMA
    },
    'additionalProperties': False
}


_WEBSOCKET_CONFIG_SCHEMA = {
    'type': 'object',
    'properties': {
        '.lq.Lobby.heatbeat': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.oauth2Auth': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.oauth2Check': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.oauth2Login': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchServerTime': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchServerSettings': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchConnectionInfo': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchPhoneLoginBind': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchClientValue': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchFriendList': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchFriendApplyList': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchMailInfo': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchDailyTask': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchReviveCoinInfo': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchTitleList': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchBagInfo': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchShopInfo': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchActivityList': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchAccountActivityData': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchVipReward': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchMonthTicketInfo': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchCommentSetting': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchAccountSettings': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchModNicknameTime': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchMisc': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchAnnouncement': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchRollingNotice': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchCharacterInfo': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchAllCommonViews': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchCollectedGameRecordList': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.loginBeat': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchGameLiveList': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchGameRecordList': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA,
        '.lq.Lobby.fetchGameRecord': _WEBSOCKET_MESSAGE_CONFIG_SCHEMA
    },
    'additionalProperties': False
}


_CONFIG_SCHEMA = {
    'type': 'object',
    'properties': {
        'http': _HTTP_CONFIG_SCHEMA,
        'websocket': _WEBSOCKET_CONFIG_SCHEMA
    },
    'additionalProperties': False
}


def _execute_action(data: dict, action: dict, r: redis_.Redis) -> None:
    if type(action) == str and action == 'NOP':
        return

    command = action['command']
    key = action['key']
    data = json.dumps(data, allow_nan=False, separators=(',', ':'))
    data = data.encode('UTF-8')

    if command == 'LPUSH':
        r.lpush(key, data)
    elif command == 'LPUSHX':
        r.lpushx(key, data)
    elif command == 'RPUSH':
        r.rpush(key, data)
    elif command == 'RPUSHX':
        r.rpushx(key, data)
    elif command == 'SET':
        options = {}
        if 'ex' in action:
            options['ex'] = action['ex']
        if 'px' in action:
            options['px'] = action['px']
        if 'nx' in action:
            options['nx'] = action['nx']
        if 'xx' in action:
            options['xx'] = action['xx']
        r.set(key, data, **options)


class RedisMirroring(object):
    def __init__(self, *, module_name: str, config: dict):
        self.__redis = redis_.Redis(module_name=module_name)
        jsonschema.validate(instance=config, schema=_CONFIG_SCHEMA)
        self.__config = config
        self.__websocket_message_queue = {}

    def on_websocket_message(
            self, flow: mitmproxy.websocket.WebSocketFlow) -> None:
        if len(flow.messages) == 0:
            raise RuntimeError(f'`len(flow.messages)` == 0')
        message = flow.messages[-1]

        if message.type != wsproto.frame_protocol.Opcode.BINARY:
            raise RuntimeError(f'{message.type}: An unsupported\
 WebSocket message type.')

        if message.from_client:
            direction = 'outbound'
        else:
            direction = 'inbound'

        content = message.content

        # TODO: b'^\x01\n.(\\.lq\\.Lobby.*)\x12' というパタンの
        # inbound WebSocket message が存在する．おそらく，レスポンスが
        # 必要ない通知メッセージと思われる．

        m = re.search(b'^(?:\x02|\x03)(..)\n.(\\.lq\\.Lobby.*?)\x12',
                      content, flags=re.DOTALL)
        if m is not None:
            # リクエストメッセージの処理．
            # 対応するレスポンスメッセージが検出されるまでメッセージを
            # キューに保存しておく．
            number = int.from_bytes(m.group(1), byteorder='little')
            if number in self.__websocket_message_queue:
                prev_request = self.__websocket_message_queue[number]
                logging.warning(f'''There is not any response message\
 for the following WebSocket request message:
direction: {prev_request['direction']}
content: {prev_request['request']}''')
            header = m.group(2).decode('UTF-8')
            self.__websocket_message_queue[number] = {
                'direction': direction,
                'header': header,
                'request': content
            }
            return
        else:
            # レスポンスメッセージ．
            # キューから対応するリクエストメッセージを探し出す．
            m = re.search(b'^(?:\x02|\x03)(..)\n\x00\x12', content,
                          flags=re.DOTALL)
            if m is None:
                raise RuntimeError(
                    f'''An unsupported WebSocket message:
direction: {direction}
content: {content}''')
            number = int.from_bytes(m.group(1), byteorder='little')
            if number not in self.__websocket_message_queue:
                raise RuntimeError(f'''An WebSocket response message\
 that does not match to any request message:
direction: {direction}
content: {content}''')
            request_direction \
                = self.__websocket_message_queue[number]['direction']
            header = self.__websocket_message_queue[number]['header']
            request = self.__websocket_message_queue[number]['request']
            response = content
            del self.__websocket_message_queue[number]

        if request_direction == 'inbound':
            if direction == 'inbound':
                raise RuntimeError('Both request and response WebSocket\
 messages are inbound.')
            assert(direction == 'outbound')
        else:
            assert(request_direction == 'outbound')
            if direction == 'outbound':
                raise RuntimeError('Both request and response WebSocket\
 messages are outbound.')
            assert(direction == 'inbound')

        match = True
        if 'websocket' not in self.__config:
            match = False
        if match and header not in self.__config['websocket']:
            match = False
        if match and request_direction != self.__config['websocket'][header]['request_direction']:
            match = False

        if match:
            request = base64.b64encode(request).decode('UTF-8')
            response = base64.b64encode(response).decode('UTF-8')
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            data = {
                'request_direction': request_direction,
                'request': request,
                'response': response,
                'timestamp': now.timestamp()
            }
            _execute_action(
                data, self.__config['websocket'][header]['action'],
                self.__redis)
            return

        logging.warning(f'''An unhandled WebSocket message:
request_direction: {request_direction}
request: {request}
response: {response}''')
