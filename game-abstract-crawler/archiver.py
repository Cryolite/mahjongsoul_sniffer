#!/usr/bin/env python3

import re
import datetime
import logging
import json
import typing
import jsonschema
import jsonschema.exceptions
import google.protobuf.json_format
import mahjongsoul_sniffer.config
import mahjongsoul_sniffer.sniffer
from mahjongsoul_sniffer.sniffer.websocket.mahjongsoul_pb2 \
    import FetchGameLiveListResponse


_GAME_LIVE_LIST_SCHEMA = {
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
                                'type': 'object'
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
                                'is_upgraded',
                                'extra_emoji'
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


def _parse(message: bytes) -> typing.List[dict]:
    result = FetchGameLiveListResponse()
    result.ParseFromString(message[3:])
    result = result.content

    result_json = google.protobuf.json_format.MessageToDict(
        result, including_default_value_fields=True,
        preserving_proto_field_name=True)
    try:
        jsonschema.validate(instance=result_json['live_list'],
                            schema=_GAME_LIVE_LIST_SCHEMA)
    except jsonschema.exceptions.ValidationError:
        raise RuntimeError(
            f'''Failed to validate the following WebSocket message:
{{'protobuf': message, 'json': result_json}}''')

    game_abstract_list = []

    for game_live in result.live_list:
        uuid = game_live.uuid

        start_time = game_live.start_time
        start_time = datetime.datetime.fromtimestamp(
            start_time, tz=datetime.timezone.utc)

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
            raise NotImplementedError(
                f'uuid == {uuid}, mode_id == {mode_id}')

        game_abstract = {
            'uuid': uuid,
            'mode': mode,
            'start_time': start_time
        }

        game_abstract_list.append(game_abstract)

    return game_abstract_list


class _S3Writer(object):
    def __init__(self):
        self.__bucket = mahjongsoul_sniffer.config.get_s3_bucket()

        key_prefix = mahjongsoul_sniffer.config.get_s3_key_prefix()
        key_prefix = re.sub('%k', 'game-abstract', key_prefix)
        self.__key_prefix = re.sub('/+$', '', key_prefix)

        with open('schema/game-abstract.json') as schema_file:
            self.__schema = json.load(schema_file)

    def write(self, game_abstract: dict) -> None:
        uuid = game_abstract['uuid']
        start_time = game_abstract['start_time']
        key_prefix = start_time.strftime(self.__key_prefix)
        key = key_prefix + '/' + uuid

        data = {
            'uuid': uuid,
            'mode': game_abstract['mode'],
            'start_time': int(start_time.timestamp())
        }
        jsonschema.validate(instance=data, schema=self.__schema)
        data = json.dumps(data, ensure_ascii=False, allow_nan=False,
                          separators=(',', ':'))
        data = data.encode('utf-8')

        self.__bucket.put_object(Key=key, Body=data)


def main():
    redis_client = mahjongsoul_sniffer.sniffer.RedisClient()
    finished = {}
    s3_writer = _S3Writer()

    while True:
        message = redis_client.blpop_websocket_message(
            key='game-abstract-list')
        redis_client.set_timestamp(key='archiver.heartbeat')
        if message['request_direction'] != 'outbound':
            raise RuntimeError(
                'An outbound WebSocket message is expected,\
 but got an inbound one.')

        message = message['response']
        game_abstract_list = _parse(message)

        for game_abstract in game_abstract_list:
            uuid = game_abstract['uuid']
            if uuid in finished:
                continue
            s3_writer.write(game_abstract)
            logging.info(f'Archived the abstract of the game {uuid}.')
            finished[uuid] = game_abstract['start_time']

        if len(finished) > 20000:
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            stale_uuid_list = []
            for uuid, start_time in finished.items():
                if now - start_time > datetime.timedelta(days=1):
                    stale_uuid_list.append(uuid)
            for stale_uuid in stale_uuid_list:
                del finished[stale_uuid]


if __name__ == '__main__':
    try:
        mahjongsoul_sniffer.config.initialize_logging(
            'game abstract archiver')
        main()
    except Exception as e:
        logging.exception('An exception was thrown.')
        raise
