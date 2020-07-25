#!/usr/bin/env python3

import datetime
import logging
import json
import jsonschema
import jsonschema.exceptions
import google.protobuf
import google.protobuf.json_format
from mitmproxy.websocket import WebSocketMessage
import redis
from mahjongsoul_sniffer.config import config
from mahjongsoul_sniffer.sniffer.websocket.mahjongsoul_pb2 \
    import (FetchGameLiveListRequest, FetchGameLiveListResponse)


with open('schema/game_abstract.json') as f:
    _game_abstract_schema = json.load(f)


def on_fetch_game_live_list(request_message: WebSocketMessage,
                            response_message: WebSocketMessage) -> None:
    logging.info('Sniffering WebSocket messages from/to'
                 ' `.lq.Lobby.fetchGameLiveList`.')

    request_string = request_message.content
    request = FetchGameLiveListRequest()
    request.ParseFromString(request_string[3:])
    request = request.content

    response_string = response_message.content
    response = FetchGameLiveListResponse()
    response.ParseFromString(response_string[3:])
    response = response.content

    game_live_list_schema = {
        'type': 'array',
        'items': {
            'type': 'object',
            'required': [
                'uuid',
                'start_time',
                'game_config',
                'players',
                'seat_list'
            ],
            'properties': {
                'uuid': {
                    'type': 'string'
                },
                'start_time': {
                    'type': 'integer',
                    'minimum': 0
                },
                'game_config': {
                    'type': 'object',
                    'required': [
                        'category',
                        'mode',
                        'meta'
                    ],
                    'properties': {
                        'category': {
                            'description': '1: 友人戦, 2: 段位戦',
                            'enum': [
                                1,
                                2
                            ]
                        },
                        'mode': {
                            'type': 'object',
                            'required': [
                                'mode',
                                'ai',
                                'extendinfo',
                                'detail_rule'
                            ],
                            'properties': {
                                'mode': {
                                    'description': '1: 東風戦, 2: 半荘戦, 4: 一局戦',
                                    'type': 'integer',
                                    'minimum': 0
                                },
                                'ai': {
                                    'title': 'CPU 参加フラグ',
                                    'description': 'false: CPU は参加していない, true: CPU が参加している',
                                    'type': 'boolean'
                                },
                                'extendinfo': {
                                    '$comment': 'TODO: 詳細不明',
                                    'const': ''
                                },
                                'detail_rule': {
                                    'type': 'object',
                                }
                            },
                            'additionalProperties': False
                        },
                        'meta': {
                            'type': 'object',
                            'required': [
                                'room_id',
                                'mode_id',
                                'contest_uid'
                            ],
                            'properties': {
                                'room_id': {
                                    'title': '友人戦ID',
                                    'type': 'integer',
                                    'minimum': 0
                                },
                                'mode_id': {
                                    'description': '2: 段位戦・銅の間・四人東風戦, '
                                                   '6: 段位戦・銀の間・四人半荘戦, '
                                                   '8: 段位戦・金の間・四人東風戦, '
                                                   '9: 段位戦・金の間・四人半荘戦, '
                                                   '11: 段位戦・玉の間・四人東風戦, '
                                                   '12: 段位戦・玉の間・四人半荘戦, '
                                                   '16: 段位戦・王座の間・四人半荘戦, '
                                                   '21: 段位戦・金の間・三人東風戦, '
                                                   '22: 段位戦・金の間・三人半荘戦, '
                                                   '23: 段位戦・玉の間・三人東風戦, '
                                                   '24: 段位戦・玉の間・三人半荘戦, '
                                                   '26: 段位戦・王座の間・三人半荘戦',
                                    'type': 'integer',
                                    'minimum': 0
                                },
                                'contest_uid': {
                                    '$comment': 'TODO: 詳細不明',
                                    'const': 0
                                }
                            },
                            'additionalProperties': False
                        }
                    },
                    'additionalProperties': False
                },
                'players': {
                    'type': 'array',
                    'minItems': 3,
                    'maxItems': 4,
                    'items': {
                        'type': 'object',
                        'required': [
                            'account_id',
                            'avatar_id',
                            'title',
                            'nickname',
                            'level',
                            'character',
                            'level3',
                            'avatar_frame',
                            'verified',
                            'views'
                        ],
                        'properties': {
                            'account_id': {
                                'type': 'integer',
                                'minimum': 0
                            },
                            'avatar_id': {
                                'type': 'integer',
                                'minimum': 0
                            },
                            'title': {
                                'type': 'integer',
                                'minimum': 0
                            },
                            'nickname': {
                                'type': 'string'
                            },
                            'level': {
                                'title': '四人戦段位',
                                'type': 'object',
                                'required': [
                                    'id',
                                    'grading_point'
                                ],
                                'properties': {
                                    'id': {
                                        'title': '四人戦段位ID',
                                        'description': '1010X: 初心, '
                                                       '1020X: 雀士, '
                                                       '1030X: 雀傑, '
                                                       '1040X: 雀豪, '
                                                       '1050X: 雀聖, '
                                                       '1060X: 魂天',
                                        'type': 'integer',
                                        'minimum': 0
                                    },
                                    'grading_point': {
                                        'title': '四人戦昇段ポイント',
                                        'type': 'integer',
                                        'minimum': 0
                                    }
                                },
                                'additionalProperties': False
                            },
                            'character': {
                                'type': 'object',
                                'required': [
                                    'id',
                                    'level',
                                    'exp',
                                    'views',
                                    'skin',
                                    'is_upgraded'
                                ],
                                'properties': {
                                    'id': {
                                        'type': 'integer',
                                        'minimum': 0,
                                    },
                                    'level': {
                                        'title': '絆レベル？',
                                        'type': 'integer',
                                        'minimum': 0
                                    },
                                    'exp': {
                                        'type': 'integer',
                                        'minimum': 0
                                    },
                                    'views': {
                                        'type': 'array',
                                        'maxItems': 0
                                    },
                                    'skin': {
                                        'type': 'integer',
                                        'minimum': 0
                                    },
                                    'is_upgraded': {
                                        'title': '契約済みフラグ',
                                        'description': 'false: キャラクタと契約してない, true: キャラクタと契約済み',
                                        'type': 'boolean'
                                    },
                                    'extra_emoji': {
                                        'type': 'array',
                                        'items': {
                                            'type': 'integer',
                                            'minimum': 0
                                        },
                                        'additionalItems': False
                                    }
                                },
                                'additionalProperties': False
                            },
                            'level3': {
                                'title': '三人戦段位',
                                'type': 'object',
                                'required': [
                                    'id',
                                    'grading_point'
                                ],
                                'properties': {
                                    'id': {
                                        'title': '三人戦段位ID',
                                        'description': '2010X: 初心, '
                                                       '2020X: 雀士, '
                                                       '2030X: 雀傑, '
                                                       '2040X: 雀豪, '
                                                       '2050X: 雀聖, '
                                                       '2060X: 魂天',
                                        'type': 'integer',
                                        'minimum': 0
                                    },
                                    'grading_point': {
                                        'title': '三人戦昇段ポイント',
                                        'type': 'integer',
                                        'minimum': 0
                                    }
                                },
                                'additionalProperties': False
                            },
                            'avatar_frame': {
                                'type': 'integer',
                                'minimum': 0
                            },
                            'verified': {
                                'type': 'integer',
                                'minimum': 0
                            },
                            'views': {
                                'title': '装飾品',
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'required': [
                                        'slot',
                                        'item_id'
                                    ],
                                    'properties': {
                                        'slot': {
                                            'description': '0: 立直棒, 1:和了演出, 2: 立直演出, 4: 立直BGM, ...',
                                            'type': 'integer',
                                            'minimum': 0
                                        },
                                        'item_id': {
                                            'type': 'integer',
                                            'minimum': 0
                                        }
                                    },
                                    'additionalProperties': False
                                },
                                'additionalItems': False
                            }
                        },
                        'additionalProperties': False
                    },
                    'additionalItems': False
                },
                'seat_list': {
                    'type': 'array',
                    'minItems': 3,
                    'maxItems': 4,
                    'items': {
                        'type': 'integer',
                        'minimum': 0
                    },
                    'additionalItems': False
                }
            },
            'additionalProperties': False
        },
        'additionalItems': False
    }

    response_json = google.protobuf.json_format.MessageToDict(
        response, including_default_value_fields=True,
        preserving_proto_field_name=True)
    try:
        jsonschema.validate(instance=response_json['live_list'],
                            schema=game_live_list_schema)
    except jsonschema.exceptions.ValidationError:
        raise RuntimeError(f'''Failed to validate the following response:
{{'protobuf': response, 'json': response_json}}''')

    r = redis.Redis(host=config.redis_host, port=config.redis_port)

    for game_live in response.live_list:
        uuid = game_live.uuid

        start_time = game_live.start_time
        start_time = datetime.datetime.fromtimestamp(start_time,
                                                     tz=datetime.timezone.utc)

        mode_id = game_live.game_config.meta.mode_id
        if mode_id == 2:
            mode = '段位戦・銅の間・四人東風戦'
        elif mode_id == 6:
            mode = '段位戦・銀の間・四人半荘戦'
        elif mode_id == 8:
            mode = '段位戦・金の間・四人東風戦'
        elif mode_id == 9:
            mode = '段位戦・金の間・四人半荘戦'
        elif mode_id == 11:
            mode = '段位戦・玉の間・四人東風戦'
        elif mode_id == 12:
            mode = '段位戦・玉の間・四人半荘戦'
        elif mode_id == 15:
            mode = '段位戦・王座の間・四人東風戦'
        elif mode_id == 16:
            mode = '段位戦・王座の間・四人半荘戦'
        elif mode_id == 21:
            mode = '段位戦・金の間・三人東風戦'
        elif mode_id == 22:
            mode = '段位戦・金の間・三人半荘戦'
        elif mode_id == 23:
            mode = '段位戦・玉の間・三人東風戦'
        elif mode_id == 24:
            mode = '段位戦・玉の間・三人半荘戦'
        elif mode_id == 26:
            mode = '段位戦・王座の間・三人半荘戦'
        else:
            raise NotImplementedError(f'uuid == {uuid}, mode_id == {mode_id}')

        game_abstract = {
            'uuid': uuid,
            'mode': mode,
            'start_time': int(start_time.timestamp())
        }
        jsonschema.validate(instance=game_abstract,
                            schema=_game_abstract_schema)
        game_abstract = json.dumps(game_abstract, ensure_ascii=False,
                                   allow_nan=False, separators=(',', ':'))

        r.rpush('game-abstract-list', game_abstract)

    timestamp = int(
        datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
    r.hset('api-timestamp', 'fetchGameLiveList', timestamp)
