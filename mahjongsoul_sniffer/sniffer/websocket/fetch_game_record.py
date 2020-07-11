#!/usr/bin/env python3

import re
import datetime
import logging
import json
import binascii
import jsonschema
import jsonschema.exceptions
import google.protobuf
import google.protobuf.json_format
from mitmproxy.websocket import WebSocketMessage
from mahjongsoul_sniffer.game_record \
    import (GameRecordPlaceholder, AccountLevel, Account, Seat, Tile,
            TingpaiInfo, ZimoDapaiOption, ZimoAngangOption, ZimoJiagangOption,
            ZimoLizhiOption, ZimoHuOption, ZimoKyushukyuhaiOption, ZimoOption,
            ZimoOptionPresence, ZhentingInfo, Zimo, Chi, Peng, Daminggang,
            Angang, Jiagang, DapaiChiOption, DapaiPengOption,
            DapaiDaminggangOption, DapaiRongOption, DapaiOption,
            DapaiOptionPresence, Dapai, Shunzi, Kezi, Minggangzi, Angangzi,
            Ming, Hupai, Hule, RoundEndByHule, PlayerResultOnNoTile, NoTile,
            Kyushukyuhai, Sifengzilianda, Turn, GameRound, GameRecord)
from mahjongsoul_sniffer.sniffer.websocket.mahjongsoul_pb2 \
    import (FetchGameRecordRequest, FetchGameRecordResponse,
            GameDetailRecords, RecordNewRound, RecordDealTile,
            RecordChiPengGang, RecordAnGangAddGang, RecordDiscardTile,
            RecordHule, RecordNoTile, RecordLiuJu)


_tile_schema = {
    'title': '牌種',
    'description': '"0m", "1m" ~ "9m", "0p", "1p" ~ "9p", "0s", "1s" ~ "9s", "1z" ~ "7z" のいずれか．',
    'type': 'string'
}


_seat_schema = {
    'title': '座席',
    'description': '0: 起家, 1: 起家の下家, 2: 起家の対面, 3: 起家の上家',
    'enum': [
        0,
        1,
        2,
        3
    ]
}


_zimo_option_schema = {
    'title': '自摸時選択肢',
    'description': '嶺上牌を含む自摸の直後，またはチー・ポンの直後に可能な操作の選択肢．',
    'oneOf': [
        {
            'title': '打牌',
            'type': 'object',
            'required': [
                'type',
                'combination'
            ],
            'properties': {
                'type': {
                    'const': 1
                },
                'combination': {
                    '$comment': 'TODO: 鳴いた時の打牌時に存在するが詳細不明．食い替えで打牌が禁止される牌か？',
                    'type': 'array',
                    'items': _tile_schema,
                    'additionalItems': False
                }
            },
            'additionalProperties': False
        },
        {
            'title': '暗槓',
            'type': 'object',
            'required': [
                'type',
                'combination'
            ],
            'properties': {
                'type': {
                    'const': 4
                },
                'combination': {
                    'type': 'array',
                    'minItems': 1,
                    'maxItems': 1,
                    'items': {
                        'description': '暗槓の対象牌4つを "|" で区切った文字列． "1m|1m|1m|1m", "0m|5m|5m|5m" など．',
                        'type': 'string'
                    },
                    'additionalItems': False
                }
            },
            'additionalProperties': False
        },
        {
            'title': '加槓',
            'type': 'object',
            'required': [
                'type',
                'combination'
            ],
            'properties': {
                'type': {
                    'const': 6
                },
                'combination': {
                    'type': 'array',
                    'minItems': 1,
                    'maxItems': 1,
                    'items': {
                        'description': '加槓の対象牌4つを "|" で区切った文字列． "1m|1m|1m|1m", "0m|5m|5m|5m" など．',
                        'type': 'string'
                    },
                    'additionalItems': False
                }
            },
            'additionalProperties': False
        },
        {
            'title': '立直',
            'type': 'object',
            'required': [
                'type',
                'combination'
            ],
            'properties': {
                'type': {
                    'const': 7
                },
                'combination': {
                    'description': '立直のために打牌する牌，つまり立直宣言牌になる牌の候補．',
                    'type': 'array',
                    'minItems': 1,
                    'items': _tile_schema,
                    'additionalItems': False
                }
            },
            'additionalProperties': False
        },
        {
            'title': '自摸和',
            'type': 'object',
            'required': [
                'type',
                'combination'
            ],
            'properties': {
                'type': {
                    'const': 8
                },
                'combination': {
                    'type': 'array',
                    'maxItems': 0
                }
            },
            'additionalProperties': False
        },
        {
            'title': '九種九牌',
            'type': 'object',
            'required': [
                'type',
                'combination'
            ],
            'properties': {
                'type': {
                    'const': 10
                },
                'combination': {
                    'type': 'array',
                    'maxItems': 0
                }
            },
            'additionalProperties': False
        }
    ]
}


def _decode_zimo_option(msg: google.protobuf.message) -> ZimoOption:
    if msg.type == 1:
        tiles = [Tile(code) for code in msg.combination]
        option = ZimoDapaiOption(tiles=tiles)
    elif msg.type == 4:
        if len(msg.combination) != 1:
            raise RuntimeError(f'msg.combination == {msg.combination}')
        tiles = [Tile(code) for code in msg.combination[0].split('|')]
        option = ZimoAngangOption(tiles=tiles)
    elif msg.type == 6:
        if len(msg.combination) != 1:
            raise RuntimeError(f'msg.combination == {msg.combination}')
        tiles = [Tile(code) for code in msg.combination[0].split('|')]
        option = ZimoJiagangOption(tiles=tiles)
    elif msg.type == 7:
        tiles = [Tile(code) for code in msg.combination]
        option = ZimoLizhiOption(tiles=tiles)
    elif msg.type == 8:
        if len(msg.combination) != 0:
            raise RuntimeError(f'msg.combination == {msg.combination}')
        option = ZimoHuOption()
    elif msg.type == 10:
        if len(msg.combination) != 0:
            raise RuntimeError(f'msg.combination == {msg.combination}')
        option = ZimoKyushukyuhaiOption()
    else:
        raise NotImplementedError(f'type == {type}')

    return ZimoOption(option=option)


_zimo_option_presence_schema = {
    'title': '自摸時選択肢提示',
    '$comment': '親の配牌直後，嶺上牌を含む自摸直後，およびチー・ポンの直後に可能な選択肢の提示．',
    'type': 'object',
    'required': [
        'seat',
        'options',
        'overtime',
        'main_time'
    ],
    'properties': {
        'seat': _seat_schema,
        'options': {
            '$comment': '立直宣言者は打牌が自動になるので空配列になる場合がある．',
            'type': 'array',
            'items': _zimo_option_schema,
            'additionalItems': False
        },
        'overtime': {
            'title': '追加考慮時間（ミリ秒）',
            'type': 'integer',
            'minimum': 0
        },
        'main_time': {
            'title': '基本考慮時間（ミリ秒）',
            'type': 'integer',
            'minimum': 0
        }
    },
    'additionalProperties': False
}


def _decode_zimo_option_presence(
        msg: google.protobuf.message) -> ZimoOptionPresence:
    seat = Seat(msg.seat)
    options = [_decode_zimo_option(option_msg) for option_msg in msg.options]
    return ZimoOptionPresence(seat=seat, options=options,
                              main_time=msg.main_time, overtime=msg.overtime)


_tingpai_schema = {
    'title': '聴牌情報',
    'required': [
        'tile',
        'has_yifan',
        'damanguan_rong',
        'fan_rong',
        'fu_rong',
        'biao_dora_count',
        'damanguan_zimo',
        'fan_zimo',
        'fu_zimo'
    ],
    'properties': {
        'tile': _tile_schema,
        'has_yifan': {
            'title': '役の有無',
            'description': 'false: 役無し, true: 和了に必要な一翻がある',
            'type': 'boolean'
        },
        'damanguan_rong': {
            'title': '出上がり役満聴牌',
            'description': 'false: 出上がり役満聴牌ではない, true: 出上がり役満聴牌である',
            'type': 'boolean'
        },
        'fan_rong': {
            'title': '栄和の場合のドラを除いた確定翻数',
            'type': 'integer',
            'minimum': 0
        },
        'fu_rong': {
            'title': '栄和の場合の符',
            'type': 'integer',
            'minimum': 25
        },
        'biao_dora_count': {
            'title': '確定ドラ数',
            'type': 'integer',
            'minimum': 0
        },
        'damanguan_zimo': {
            'title': '自模り役満聴牌',
            'description': 'false: 自模り役満聴牌ではない, true: 自模り役満聴牌である',
            'type': 'boolean'
        },
        'fan_zimo': {
            'title': '自摸和の場合のドラを除いた確定翻数',
            'type': 'integer',
            'minimum': 0
        },
        'fu_zimo': {
            'title': '自摸和の場合の符',
            'type': 'integer',
            'minimum': 20
        }
    },
    'additionalProperties': False
}


def _decode_tingpai_info(message: google.protobuf.message) -> TingpaiInfo:
    return TingpaiInfo(
        tile=Tile(message.tile), has_yifan=message.has_yifan,
        fu_zimo=message.fu_zimo, fan_zimo=message.fan_zimo,
        damanguan_zimo=message.damanguan_zimo, fu_rong=message.fu_rong,
        fan_rong=message.fan_rong, damanguan_rong=message.damanguan_rong,
        biao_dora_count=message.biao_dora_count)


def _on_new_round(data: bytes) -> GameRound:
    new_round = RecordNewRound()
    new_round.ParseFromString(data)
    if new_round.header != '.lq.RecordNewRound':
        raise RuntimeError("Failed to parse `.lq.RecordNewRound'.")
    new_round = new_round.content
    new_round_json = google.protobuf.json_format.MessageToDict(
        new_round, including_default_value_fields=True,
        preserving_proto_field_name=True)

    new_round_schema = {
        'title': '開局',
        'type': 'object',
        'required': [
            'chang',
            'ju',
            'ben',
            'dora',
            'scores',
            'lizhibang',
            'qipai0',
            'qipai1',
            'qipai2',
            'qipai3',
            'tingpai_list',
            'option_presence',
            'paishan_code',
            'paishan',
            'left_tile_count',
            'doras',
            'opened_tiles'
        ],
        'properties': {
            'chang': {
                'title': '場',
                'description': '0: 東場, 1: 南場, 2: 西場',
                'enum': [0, 1, 2]
            },
            'ju': {
                'title': '局',
                'description': '0: 1局目, 1: 2局目, 2: 3局目, 3: 4局目',
                'enum': [0, 1, 2, 3]
            },
            'ben': {
                'title': 'n本場',
                'description': '0: 0本場, 1: 1本場, ...',
                'type': 'integer',
                'minimum': 0
            },
            'dora': {
                '$comment': 'TODO: ドラは `doras` に記録されるのでこのキーの詳細が不明．',
                'const': ''
            },
            'scores': {
                'title': '開局時各家スコア',
                'description': '0: 起家, 1: 起家の下家, 2: 起家の対面, 3: 起家の上家',
                'type': 'array',
                'minItems': 4,
                'maxItems': 4,
                'items': {
                    'type': 'integer'
                },
                'additionalItems': False
            },
            'lizhibang': {
                'title': '供託本数',
                'type': 'integer',
                'minimum': 0
            },
            'qipai0': {
                'title': '起家の配牌',
                '$comment': '起牌 (qipai) = 配牌',
                'type': 'array',
                'minItems': 13,
                'maxItems': 14,
                'items': _tile_schema,
                'additionalItems': False
            },
            'qipai1': {
                'title': '起家の下家の配牌',
                '$comment': '起牌 (qipai) = 配牌',
                'type': 'array',
                'minItems': 13,
                'maxItems': 14,
                'items': _tile_schema,
                'additionalItems': False
            },
            'qipai2': {
                'title': '起家の対面の配牌',
                '$comment': '起牌 (qipai) = 配牌',
                'type': 'array',
                'minItems': 13,
                'maxItems': 14,
                'items': _tile_schema,
                'additionalItems': False
            },
            'qipai3': {
                'title': '起家の上家の配牌',
                '$comment': '起牌 (qipai) = 配牌',
                'type': 'array',
                'minItems': 13,
                'maxItems': 14,
                'items': _tile_schema,
                'additionalItems': False
            },
            'tingpai_list': {
                'title': '配牌時の各家の聴牌情報',
                'type': 'array',
                'maxItems': 4,
                'items': {
                    'type': 'object',
                    'required': [
                        'seat',
                        'tingpai'
                    ],
                    'properties': {
                        'seat': _seat_schema,
                        'tingpai': {
                            'type': 'array',
                            'minItems': 1,
                            'maxItems': 1,
                            'items': _tingpai_schema
                        }
                    },
                    'additionalProperties': False
                },
                'additionalItems': False
            },
            'option_presence': _zimo_option_presence_schema,
            'paishan_code': {
                'title': '牌山コード',
                'type': 'string'
            },
            'paishan': {
                'title': '牌山',
                'type': 'string'
            },
            'left_tile_count': {
                'title': '残り自摸牌数',
                'enum': [
                    69
                ]
            },
            'doras': {
                'title': '表ドラ表示牌',
                'type': 'array',
                'minItems': 1,
                'maxItems': 1,
                'items': _tile_schema,
                'additionalItems': False
            },
            'opened_tiles': {
                '$comment': 'TODO: 詳細不明．',
                'type': 'array',
                'minItems': 4,
                'maxItems': 4,
                'items': {
                    'type': 'object',
                    'required': [
                        'seat',
                        'tiles',
                        'count'
                    ],
                    'properties': {
                        'seat': _seat_schema,
                        'tiles': {
                            'type': 'array',
                            'maxItems': 0
                        },
                        'count': {
                            'type': 'array',
                            'maxItems': 0
                        }
                    },
                    'additionalProperties': False
                },
                'additionalItems': False
            }
        },
        'additionalProperties': False
    }

    try:
        jsonschema.validate(instance=new_round_json, schema=new_round_schema)
    except jsonschema.exceptions.ValidationError:
        raise RuntimeError(
            f'''Failed to validate the following NewRound data:
{{'protobuf': new_round, 'json': new_round_json}}''')

    chang = None
    ju = None
    ben = None
    try:
        if new_round.chang == 0:
            chang = '東'
        elif new_round.chang == 1:
            chang = '南'
        elif new_round.chang == 2:
            chang = '西'
        else:
            raise NotImplementedError(f'chang == {chang}')

        ju = new_round.ju
        ben = new_round.ben

        initial_scores = [initial_score for initial_score in new_round.scores]

        qipai_list = []
        qipai_list.append([Tile(code) for code in new_round.qipai0])
        qipai_list.append([Tile(code) for code in new_round.qipai1])
        qipai_list.append([Tile(code) for code in new_round.qipai2])
        qipai_list.append([Tile(code) for code in new_round.qipai3])

        paishan = []
        if len(new_round.paishan) % 2 != 0:
            raise RuntimeError(f'An invalid paishan: {new_round.paishan}')
        for i in range(len(new_round.paishan) // 2):
            code = new_round.paishan[2 * i:2 * i + 2]
            tile = Tile(code)
            paishan.append(tile)

        dora = Tile(new_round.doras[0])

        tingpai_list = []
        for e in new_round.tingpai_list:
            seat = Seat(e.seat)
            tingpai = _decode_tingpai_info(e.tingpai[0])
            tingpai_list.append((seat, tingpai))

        option_presence = _decode_zimo_option_presence(new_round.option_presence)

        return GameRound(
            chang=chang, ju=ju, ben=ben, lizhibang=new_round.lizhibang,
            initial_scores=initial_scores, qipai_list=qipai_list,
            paishan=paishan, paishan_code=new_round.paishan_code,
            dora=dora, left_tile_count=new_round.left_tile_count,
            tingpai_list=tingpai_list, option_presence=option_presence)
    except Exception as e:
        error_message = ''
        if chang is not None and ju is not None and ben is not None:
            error_message += f'{chang}{ju + 1}局{ben}本場: '
        error_message += f'''Failed to decode the following NewRound data:
{{'protobuf': new_round, 'json': new_round_json}}'''
        raise RuntimeError(error_message)


_prev_lizhi_schema = {
    'title': '直前の立直に対する立直棒演出',
    'type': 'object',
    'required': [
        'seat',
        'new_score',
        'lizhibang'
    ],
    'properties': {
        'seat': _seat_schema,
        'new_score': {
            'type': 'integer',
            'minimum': 0
        },
        'lizhibang': {
            '$comment': '立直棒の種類か？',
            'type': 'integer',
            'minimum': 0
        }
    }
}


_zhenting_schema = {
    'title': '振聴フラグ',
    'description': 'false: 振聴ではない, true: 振聴である',
    'type': 'array',
    'minItems': 4,
    'maxItems': 4,
    'items': {
        'type': 'boolean'
    },
    'additionalItems': False
}


def _decode_zhenting_info(msg: google.protobuf.message) -> ZhentingInfo:
    flags = [flag for flag in msg]
    return ZhentingInfo(flags=flags)


def _on_deal_tile(data: bytes, game_round: GameRound) -> None:
    deal_tile = RecordDealTile()
    deal_tile.ParseFromString(data)
    if deal_tile.header != '.lq.RecordDealTile':
        raise RuntimeError("Failed to parse `.lq.RecordDealTile'.")
    deal_tile = deal_tile.content
    deal_tile_json = google.protobuf.json_format.MessageToDict(
        deal_tile, including_default_value_fields=True,
        preserving_proto_field_name=True)

    deal_tile_schema = {
        'title': '自摸',
        'type': 'object',
        'required': [
            'seat',
            'tile',
            'left_tile_count',
            'doras',
            'zhenting',
            'option_presence',
            'tile_state'
        ],
        'properties': {
            'seat': _seat_schema,
            'tile': _tile_schema,
            'left_tile_count': {
                'title': '残り自摸牌数',
                'type': 'integer',
                'minimum': 0
            },
            'prev_lizhi': _prev_lizhi_schema,
            'doras': {
                'title': 'ドラ',
                'description': '嶺上牌を自摸った際に新ドラを表示する必要があるために存在する．新旧の全ドラを含む．',
                'type': 'array',
                'items': _tile_schema,
                'additionalItems': False
            },
            'zhenting': _zhenting_schema,
            'option_presence': _zimo_option_presence_schema,
            'tile_state': {
                '$comment': '詳細不明．',
                'const': 0
            }
        },
        'additionalProperties': False
    }

    try:
        jsonschema.validate(instance=deal_tile_json, schema=deal_tile_schema)
    except jsonschema.exceptions.ValidationError:
        raise RuntimeError(
            f'''Failed to validate the following DealTile data:
{{'protobuf': deal_tile, 'json': deal_tile_json}}''')

    try:
        seat = Seat(deal_tile.seat)
        doras = [Tile(code) for code in deal_tile.doras]
        tile = Tile(deal_tile.tile)
        option_presence = _decode_zimo_option_presence(deal_tile.option_presence)
        zhenting = _decode_zhenting_info(deal_tile.zhenting)
        zimo = Zimo(seat=seat, doras=doras, tile=tile,
                    left_tile_count=deal_tile.left_tile_count,
                    option_presence=option_presence, zhenting=zhenting)
        turn = Turn(zimo)
        game_round.append_turn(turn)
    except Exception as e:
        raise RuntimeError(
            f'''Failed to decode the following DealTile data:
{{'protobuf': deal_tile, 'json': deal_tile_json}}''')


def _on_chi_peng_gang(data: bytes, game_round: GameRound) -> None:
    chi_peng_gang = RecordChiPengGang()
    chi_peng_gang.ParseFromString(data)
    if chi_peng_gang.header != '.lq.RecordChiPengGang':
        raise RuntimeError("Failed to parse `.lq.RecordChiPengGang'.")
    chi_peng_gang = chi_peng_gang.content
    chi_peng_gang_json = google.protobuf.json_format.MessageToDict(
        chi_peng_gang, including_default_value_fields=True,
        preserving_proto_field_name=True)

    chi_schema = {
        'title': 'チー',
        'type': 'object',
        'required': [
            'seat',
            'type',
            'tiles',
            'froms',
            'zhenting',
            'option_presence'
        ],
        'properties': {
            'seat': _seat_schema,
            'type': {
                'const': 0
            },
            'tiles': {
                'title': 'チーの対象牌',
                'description': '0番目と1番目の要素が手牌にあった牌．2番目の要素が鳴いた牌．',
                'type': 'array',
                'minItems': 3,
                'maxItems': 3,
                'items': _tile_schema,
                'additionalItems': False
            },
            'froms': {
                'title': 'チーの対象となった牌がどの席から出たか',
                'description': '0番目と1番目の要素は自席番号，2番目の要素が上家の席番号になる．',
                'type': 'array',
                'minItems': 3,
                'maxItems': 3,
                'items': _seat_schema,
                'additionalItems': False
            },
            'prev_lizhi': _prev_lizhi_schema,
            'zhenting': _zhenting_schema,
            'option_presence': _zimo_option_presence_schema,
            'tile_states': {
                '$comment': 'TODO: 詳細を調査すること．',
                'type': 'array',
                'items': {
                    'type': 'integer',
                    'minimum': 0
                },
                'additionalItems': False
            }
        },
        'additionalProperties': False
    }

    peng_schema = {
        'title': 'ポン',
        'type': 'object',
        'required': [
            'seat',
            'type',
            'tiles',
            'froms',
            'zhenting',
            'option_presence'
        ],
        'properties': {
            'seat': _seat_schema,
            'type': {
                'const': 1
            },
            'tiles': {
                'title': 'ポンの対象牌',
                'type': 'array',
                'minItems': 3,
                'maxItems': 3,
                'items': _tile_schema,
                'additionalItems': False
            },
            'froms': {
                'title': 'ポンの対象となった牌がどの席から出たか',
                'description': '0番目と1番目の要素は自席番号，2番目の要素が対象の牌を打牌した席番号になる．',
                'type': 'array',
                'minItems': 3,
                'maxItems': 3,
                'items': _seat_schema,
                'additionalItems': False
            },
            'prev_lizhi': _prev_lizhi_schema,
            'zhenting': _zhenting_schema,
            'option_presence': _zimo_option_presence_schema,
            'tile_states': {
                '$comment': 'TODO: 詳細を調査すること．',
                'type': 'array',
                'items': {
                    'type': 'integer',
                    'minimum': 0
                },
                'additionalItems': False
            }
        },
        'additionalProperties': False
    }

    gang_schema = {
        'title': '大明槓',
        'type': 'object',
        'required': [
            'seat',
            'type',
            'tiles',
            'froms',
            'zhenting'
        ],
        'properties': {
            'seat': _seat_schema,
            'type': {
                'const': 2
            },
            'tiles': {
                'title': '大明槓の対象牌',
                'type': 'array',
                'minItems': 4,
                'maxItems': 4,
                'items': _tile_schema,
                'additionalItems': False
            },
            'froms': {
                'title': '大明槓の対象となった牌がどの席から出たか',
                'description': '0番目から2番目の要素は自席番号，3番目の要素が対象の牌を打牌した席番号になる．',
                'type': 'array',
                'minItems': 4,
                'maxItems': 4,
                'items': _seat_schema,
                'additionalItems': False
            },
            'prev_lizhi': _prev_lizhi_schema,
            'zhenting': _zhenting_schema,
            'tile_states': {
                '$comment': 'TODO: 詳細を調査すること．',
                'type': 'array',
                'items': {
                    'type': 'integer',
                    'minimum': 0
                },
                'additionalItems': False
            }
        },
        'additionalProperties': False
    }

    chi_peng_gang_schema = {
        'oneOf': [
            chi_schema,
            peng_schema,
            gang_schema
        ]
    }

    try:
        jsonschema.validate(instance=chi_peng_gang_json,
                            schema=chi_peng_gang_schema)
    except jsonschema.exceptions.ValidationError:
        raise RuntimeError(
            f'''Failed to validate the following ChiPengGang data:
{{'protobuf': chi_peng_gang, 'json': chi_peng_gang_json}}''')

    try:
        seat = Seat(chi_peng_gang.seat)
        tiles = [Tile(code) for code in chi_peng_gang.tiles]
        froms = [Seat(index) for index in chi_peng_gang.froms]
        zhenting = _decode_zhenting_info(chi_peng_gang.zhenting)

        if chi_peng_gang.type == 0:
            option_presence = _decode_zimo_option_presence(
                chi_peng_gang.option_presence)
            chi = Chi(seat=seat, tiles=tiles, froms=froms, zhenting=zhenting,
                      option_presence=option_presence)
            turn = Turn(turn=chi)
        elif chi_peng_gang.type == 1:
            option_presence = _decode_zimo_option_presence(
                chi_peng_gang.option_presence)
            peng = Peng(seat=seat, tiles=tiles, froms=froms, zhenting=zhenting,
                        option_presence=option_presence)
            turn = Turn(turn=peng)
        elif chi_peng_gang.type == 2:
            daminggang = Daminggang(seat=seat, tiles=tiles, froms=froms,
                                    zhenting=zhenting)
            turn = Turn(turn=daminggang)
        else:
            raise NotImplementedError(f'type == {chi_peng_gang.type}')

        game_round.append_turn(turn)
    except Exception as e:
        raise RuntimeError(
            f'''Failed to decode the following ChiPengGang data:
{{'protobuf': chi_peng_gang, 'json': chi_peng_gang_json}}''')


def _on_an_gang_add_gang(data: bytes, game_round: GameRound) -> None:
    an_gang_add_gang = RecordAnGangAddGang()
    an_gang_add_gang.ParseFromString(data)
    if an_gang_add_gang.header != '.lq.RecordAnGangAddGang':
        raise RuntimeError("Failed to parse `.lq.RecordAnGangAddGang'.")
    an_gang_add_gang = an_gang_add_gang.content
    an_gang_add_gang_json = google.protobuf.json_format.MessageToDict(
        an_gang_add_gang, including_default_value_fields=True,
        preserving_proto_field_name=True)

    an_gang_schema = {
        'title': '暗槓',
        'type': 'object',
        'required': [
            'seat',
            'type',
            'tiles',
            'doras',
            'option_presence'
        ],
        'properties': {
            'seat': _seat_schema,
            'type': {
                'const': 3
            },
            'tiles': _tile_schema,
            'doras': {
                '$comment': 'TODO: 詳細不明．',
                'type': 'array',
                'maxItems': 0
            },
            'option_presence': {
                'type': 'array',
                'maxItems': 0
            }
        },
        'additionalProperties': False
    }

    add_gang_schema = {
        'title': '加槓',
        'type': 'object',
        'required': [
            'seat',
            'type',
            'tiles',
            'doras',
            'option_presence'
        ],
        'properties': {
            'seat': _seat_schema,
            'type': {
                'const': 2
            },
            'tiles': _tile_schema,
            'doras': {
                '$comment': 'TODO: 詳細不明．',
                'type': 'array',
                'maxItems': 0
            },
            'option_presence': {
                'type': 'array',
                'maxItems': 0
            }
        },
        'additionalProperties': False
    }

    an_gang_add_gang_schema = {
        'oneOf': [
            an_gang_schema,
            add_gang_schema
        ]
    }

    try:
        jsonschema.validate(instance=an_gang_add_gang_json,
                            schema=an_gang_add_gang_schema)
    except jsonschema.exceptions.ValidationError:
        raise RuntimeError(
            f'''Failed to validate the following AnGangAddGang data:
{{'protobuf': an_gang_add_gang, 'json': an_gang_add_gang_json}}''')

    seat = Seat(an_gang_add_gang.seat)

    try:
        if an_gang_add_gang.type == 3:
            tile = Tile(an_gang_add_gang.tiles)
            angang = Angang(seat=seat, tile=tile)
            turn = Turn(angang)
        elif an_gang_add_gang.type == 2:
            tile = Tile(an_gang_add_gang.tiles)
            jiagang = Jiagang(seat=seat, tile=tile)
            turn = Turn(jiagang)
        else:
            raise NotImplementedError(f'type == {an_gang_add_gang.type}')

        game_round.append_turn(turn)
    except Exception as e:
        raise RuntimeError(
            f'''Failed to decode the following AnGangAddGang data:
{{'protobuf': an_gang_add_gang, 'json': an_gang_add_gang_json}}''')


def _on_discard_tile(data: bytes, game_round: GameRound) -> None:
    discard_tile = RecordDiscardTile()
    discard_tile.ParseFromString(data)
    if discard_tile.header != '.lq.RecordDiscardTile':
        raise RuntimeError("Failed to parse `.lq.RecordDiscardTile'.")
    discard_tile = discard_tile.content
    discard_tile_json = google.protobuf.json_format.MessageToDict(
        discard_tile, including_default_value_fields=True,
        preserving_proto_field_name=True)

    chi_option_schema = {
        'title': 'チーの選択肢',
        'type': 'object',
        'required': [
            'type',
            'combination'
        ],
        'properties': {
            'type': {
                'const': 2
            },
            'combination': {
                'type': 'array',
                'minItems': 1,
                'items': {
                    'description': 'チーの対象となる手牌2つを "|" で区切った文字列．',
                    'type': 'string'
                },
                'additionalItems': False
            }
        },
        'additionalProperties': False
    }

    peng_option_schema = {
        'title': 'ポンの選択肢',
        'type': 'object',
        'required': [
            'type',
            'combination'
        ],
        'properties': {
            'type': {
                'const': 3
            },
            'combination': {
                'type': 'array',
                'minItems': 1,
                'items': {
                    'description': 'ポンの対象となる手牌2つを "|" で区切った文字列．',
                    'type': 'string'
                },
                'additionalItems': False
            }
        },
        'additionalProperties': False
    }

    daminggang_option_schema = {
        'title': '大明槓の選択肢',
        'type': 'object',
        'required': [
            'type',
            'combination'
        ],
        'properties': {
            'type': {
                'const': 5
            },
            'combination': {
                'type': 'array',
                'minItems': 1,
                'maxItems': 1,
                'items': {
                    'description': '大明槓の対象となる手牌3つを|で区切った文字列．',
                    'type': 'string'
                },
                'additionalItems': False
            }
        },
        'additionalProperties': False
    }

    rong_option_schema = {
        'title': '栄和の選択肢',
        'type': 'object',
        'required': [
            'type',
            'combination'
        ],
        'properties': {
            'type': {
                'const': 9
            },
            'combination': {
                'type': 'array',
                'maxItems': 0
            }
        },
        'additionalProperties': False
    }

    def decode_dapai_option(msg: google.protobuf.message) -> DapaiOption:
        if msg.type == 2:
            tiles_list = []
            for e in msg.combination:
                codes = e.split('|')
                tiles = [Tile(code) for code in codes]
                tiles_list.append(tiles)
            option = DapaiChiOption(tiles_list=tiles_list)
        elif msg.type == 3:
            tiles_list = []
            for e in msg.combination:
                codes = e.split('|')
                tiles = [Tile(code) for code in codes]
                tiles_list.append(tiles)
            option = DapaiPengOption(tiles_list=tiles_list)
        elif msg.type == 5:
            codes = msg.combination[0].split('|')
            tiles = [Tile(code) for code in codes]
            option = DapaiDaminggangOption(tiles=tiles)
        elif msg.type == 9:
            option = DapaiRongOption()

        return DapaiOption(option=option)

    dapai_option_presence_schema = {
        'title': '打牌に対する選択肢提示',
        'type': 'object',
        'required': [
            'seat',
            'options',
            'overtime',
            'main_time'
        ],
        'properties': {
            'seat': _seat_schema,
            'options': {
                'type': 'array',
                'minItems': 1,
                'items': {
                    'oneOf': [
                        chi_option_schema,
                        peng_option_schema,
                        daminggang_option_schema,
                        rong_option_schema
                    ]
                },
                'additionalItems': False
            },
            'overtime': {
                'title': '追加考慮時間',
                'type': 'integer',
                'minimum': 0
            },
            'main_time': {
                'title': '考慮時間',
                'type': 'integer',
                'minimum': 0
            }
        },
        'additionalProperties': False
    }

    def decode_dapai_option_presence(
            msg: google.protobuf.message) -> DapaiOptionPresence:
        seat = Seat(msg.seat)
        options = [decode_dapai_option(option_msg) for option_msg in msg.options]
        return DapaiOptionPresence(seat=seat, options=options,
                                   main_time=msg.main_time,
                                   overtime=msg.overtime)

    discard_tile_schema = {
        'type': 'object',
        'required': [
            'seat',
            'tile',
            'lizhi',
            'moqie',
            'zhenting',
            'tingpai_list',
            'doras',
            'double_lizhi',
            'option_presence_list',
        ],
        'properties': {
            'seat': _seat_schema,
            'tile': _tile_schema,
            'lizhi': {
                'title': '立直フラグ',
                'description': 'false: 立直宣言ではない, true: 立直宣言である',
                'type': 'boolean'
            },
            'moqie': {
                'title': '自摸切り',
                'description': 'false: 手出し, true: 自摸切り',
                'type': 'boolean'
            },
            'zhenting': _zhenting_schema,
            'tingpai_list': {
                'type': 'array',
                'items': _tingpai_schema,
                'additionalItems': False
            },
            'doras': {
                'title': 'ドラ',
                'description': '嶺上牌の自摸後の打牌時にのみ要素が存在する．新旧全てのドラを含む．',
                'type': 'array',
                'items': _tile_schema,
                'additionalItems': False
            },
            'double_lizhi': {
                'title': 'ダブル立直',
                'description': 'false: ダブル立直宣言ではない, true: ダブル立直宣言である',
                'type': 'boolean'
            },
            'option_presence_list': {
                'type': 'array',
                'items': dapai_option_presence_schema,
                'additionalItems': False
            },
            'tile_state': {
                '$comment': 'TODO: 詳細を調査する．',
                'type': 'integer',
                'minimum': 0
            }
        },
        'additionalProperties': False
    }

    try:
        jsonschema.validate(instance=discard_tile_json,
                            schema=discard_tile_schema)
    except jsonschema.exceptions.ValidationError:
        raise RuntimeError(
            f'''Failed to validate the following DiscardTile data:
{{'protobuf': discard_tile, 'json': discard_tile_json}}''')

    try:
        seat = Seat(discard_tile.seat)
        tile = Tile(discard_tile.tile)
        tingpai_list = [
            _decode_tingpai_info(e) for e in discard_tile.tingpai_list
        ]
        zhenting = _decode_zhenting_info(discard_tile.zhenting)
        option_presence_list = [
            decode_dapai_option_presence(e) for e in discard_tile.option_presence_list
        ]
        doras = [Tile(code) for code in discard_tile.doras]

        dapai = Dapai(seat=seat, tile=tile, moqie=discard_tile.moqie,
                      lizhi=discard_tile.lizhi,
                      double_lizhi=discard_tile.double_lizhi,
                      tingpai_list=tingpai_list, zhenting=zhenting,
                      option_presence_list=option_presence_list, doras=doras)
        turn = Turn(dapai)
        game_round.append_turn(turn)
    except Exception as e:
        raise RuntimeError(
            f'''Failed to decode the following DiscardTile data:
{{'protobuf': discard_tile, 'json': discard_tile_json}}''')


_hupai_titles = [
    '',
    '門前清自摸和',
    '立直',
    '槍槓',
    '嶺上開花',
    '海底摸月',
    '河底撈魚',
    '役牌白',
    '役牌發',
    '役牌中',
    '役牌:自風牌',
    '役牌:場風牌',
    '断幺九',
    '一盃口',
    '平和',
    '混全帯幺九',
    '一気通貫',
    '三色同順',
    'ダブル立直',
    '三色同刻',
    '三槓子',
    '対々和',
    '三暗刻',
    '小三元',
    '混老頭',
    '七対子',
    '純全帯幺九',
    '混一色',
    '二盃口',
    '清一色',
    '一発',
    'ドラ',
    '赤ドラ',
    '裏ドラ',
    '流し満貫',
    '天和',
    '地和',
    '大三元',
    '四暗刻',
    '字一色',
    '緑一色',
    '清老頭',
    '国士無双',
    '小四喜',
    '四槓子',
    '九蓮宝燈',
    '純正九蓮宝燈',
    '四暗刻単騎',
    '国士無双十三面待ち',
    '大四喜'
]


_fan_titles = [
    '',
    '満貫',
    '跳満',
    '倍満',
    '三倍満',
    '役満',
    '二倍役満',
    '三倍役満',
    '四倍役満',
    '五倍役満',
]


def _on_hule(data: bytes, game_round: GameRound) -> None:
    hule = RecordHule()
    hule.ParseFromString(data)
    if hule.header != '.lq.RecordHule':
        raise RuntimeError("Failed to parse `.lq.RecordHule'.")
    hule = hule.content
    hule_json = google.protobuf.json_format.MessageToDict(
        hule, including_default_value_fields=True,
        preserving_proto_field_name=True)

    hule_schema = {
        'title': '和了',
        'type': 'object',
        'required': [
            'hule_list',
            'old_scores',
            'delta_scores',
            'wait_timeout',
            'new_scores',
            'gameend',
            'doras'
        ],
        'properties': {
            'hule_list': {
                'type': 'array',
                'minItems': 1,
                'maxItems': 3,
                'items': {
                    'type': 'object',
                    'required': [
                        'hand',
                        'ming_list',
                        'hupai',
                        'seat',
                        'zimo',
                        'zhuangjia',
                        'lizhi',
                        'doras',
                        'li_doras',
                        'damanguan',
                        'fan',
                        'fans',
                        'fu',
                        'title',
                        'point_rong',
                        'point_zimo_zhuangjia',
                        'point_zimo_sanjia',
                        'fan_title_id',
                        'point_sum'
                    ],
                    'properties': {
                        'hand': {
                            'title': '和了時の手牌',
                            'type': 'array',
                            'minItems': 1,
                            'maxItems': 13,
                            'items': _tile_schema,
                            'additionalItems': False
                        },
                        'ming_list': {
                            'title': '和了時の副露牌',
                            'description': '"shunzi(X,Y,Z)": チー, "kezi(X,Y,Z)": ポン, "minggang(X,Y,Z,W)": 明槓, "angang(X,Y,Z,W)": 暗槓',
                            'type': 'array',
                            'maxItems': 4,
                            'items': {
                                'type': 'string'
                            },
                            'additionalItems': False
                        },
                        'hupai': _tile_schema,
                        'seat': _seat_schema,
                        'zimo': {
                            'title': '自模和フラグ',
                            'type': 'boolean'
                        },
                        'zhuangjia': {
                            'title': '庄家（親）フラグ',
                            'type': 'boolean'
                        },
                        'lizhi': {
                            'title': '立直フラグ',
                            'type': 'boolean'
                        },
                        'doras': {
                            'title': '表ドラ',
                            'type': 'array',
                            'minItems': 1,
                            'maxItems': 5,
                            'items': _tile_schema,
                            'additionalItems': False
                        },
                        'li_doras': {
                            'title': '裏ドラ',
                            'type': 'array',
                            'maxItems': 5,
                            'items': _tile_schema,
                            'additionalItems': False
                        },
                        'damanguan': {
                            'title': '役満フラグ',
                            'description': 'false: 三倍満以下, true: 役満以上',
                            'type': 'boolean'
                        },
                        'fan': {
                            'title': '翻数',
                            'type': 'integer',
                            'minimum': 1
                        },
                        'fans': {
                            'title': '役',
                            'type': 'array',
                            'minItems': 1,
                            'items': {
                                'type': 'object',
                                'required': [
                                    'name',
                                    'val',
                                    'id'
                                ],
                                'properties': {
                                    'name': {
                                        '$comment': '詳細不明．',
                                        'const': ''
                                    },
                                    'val': {
                                        'title': '役毎の翻数',
                                        'description': '裏ドラの場合に0がありうる．',
                                        'type': 'integer',
                                        'minimum': 0
                                    },
                                    'id': {
                                        'title': '役ID',
                                        'type': 'integer',
                                        'minimum': 1
                                    }
                                },
                                'additionalProperties': False
                            },
                            'additionalItems': False
                        },
                        'fu': {
                            'title': '符',
                            'type': 'integer',
                            'minimum': 20
                        },
                        'title': {
                            '$comment': 'TODO: 詳細不明．',
                            'const': ''
                        },
                        'point_rong': {
                            'title': '栄和の支払い',
                            'type': 'integer',
                            'minimum': 0
                        },
                        'point_zimo_zhuangjia': {
                            'title': '散家（子）の自摸和の場合の庄家（親）の支払い',
                            'type': 'integer',
                            'minimum': 0
                        },
                        'point_zimo_sanjia': {
                            'title': '自摸和の場合の散家（子）の支払い',
                            'type': 'integer',
                            'minimum': 0
                        },
                        'fan_title_id': {
                            'description': '1: 満貫, 2: 跳満, 3: 倍満, 4: 三倍満, 5: 役満',
                            'type': 'integer',
                            'minimum': 0
                        },
                        'point_sum': {
                            '$comment': 'TODO: 詳細不明．',
                            'type': 'integer',
                            'minimum': 0
                        }
                    },
                    'additionalProperties': False
                },
                'additionalItems': False
            },
            'old_scores': {
                'title': '清算前点数',
                'type': 'array',
                'minItems': 4,
                'maxItems': 4,
                'items': {
                    'type': 'integer'
                },
                'additionalItems': False
            },
            'delta_scores': {
                'title': '点数収支',
                'type': 'array',
                'minItems': 4,
                'maxItems': 4,
                'items': {
                    'type': 'integer'
                },
                'additionalItems': False
            },
            'wait_timeout': {
                '$comment': 'TODO: 詳細不明．',
                'const': 0
            },
            'new_scores': {
                'title': '清算後点数',
                'type': 'array',
                'minItems': 4,
                'maxItems': 4,
                'items': {
                    'type': 'integer'
                },
                'additionalItems': False
            },
            'gameend': {
                '$comment': 'TODO: 詳細不明．',
                'type': 'object',
                'required': [
                    'scores'
                ],
                'properties': {
                    'scores': {
                        'type': 'array',
                        'maxItems': 0
                    }
                },
                'additionalProperties': False
            },
            'doras': {
                '$comment': 'TODO: 詳細不明．',
                'type': 'array',
                'maxItems': 0
            }
        },
        'additionalProperties': False
    }

    try:
        jsonschema.validate(instance=hule_json,
                            schema=hule_schema)
    except jsonschema.exceptions.ValidationError:
        raise RuntimeError(
            f'''Failed to validate the following Hule data:
{{'protobuf': hule, 'json': hule_json}}''')

    def decode_hule(msg: google.protobuf.message) -> Hule:
        seat = Seat(msg.seat)
        hand = [Tile(code) for code in msg.hand]

        ming_list = []
        for ming in msg.ming_list:
            m = re.search('^shunzi\\(([^)]+)\\)$', ming)
            if m is not None:
                codes = m.group(1).split(',')
                tiles = [Tile(code) for code in codes]
                shunzi = Shunzi(tiles=tiles)
                ming = Ming(ming=shunzi)
                ming_list.append(ming)
                continue

            m = re.search('^kezi\\(([^)]+)\\)$', ming)
            if m is not None:
                codes = m.group(1).split(',')
                tiles = [Tile(code) for code in codes]
                kezi = Kezi(tiles=tiles)
                ming = Ming(ming=kezi)
                ming_list.append(ming)
                continue

            m = re.search('^minggang\\(([^)]+)\\)$', ming)
            if m is not None:
                codes = m.group(1).split(',')
                tiles = [Tile(code) for code in codes]
                gangzi = Minggangzi(tiles=tiles)
                ming = Ming(ming=gangzi)
                ming_list.append(ming)
                continue

            m = re.search('^angang\\(([^)]+)\\)$', ming)
            if m is not None:
                codes = m.group(1).split(',')
                tiles = [Tile(code) for code in codes]
                gangzi = Angangzi(tiles=tiles)
                ming = Ming(ming=gangzi)
                ming_list.append(ming)
                continue

            raise NotImplementedError(f'ming == {ming}')

        hupai =  Tile(msg.hupai)
        doras = [Tile(code) for code in msg.doras]
        li_doras = [Tile(code) for code in msg.li_doras]

        hupai_list = []
        for e in msg.fans:
            if e.id == 31 and e.val == 0:
                # ドラ0
                continue
            if e.id == 32 and e.val == 0:
                # 赤ドラ0
                continue
            if e.id == 33 and e.val == 0:
                # 裏ドラ0
                continue
            hupai_title = _hupai_titles[e.id]
            h = Hupai(title=hupai_title, fan=e.val)
            hupai_list.append(h)

        if msg.fan_title_id == 0:
            fan_title = None
        else:
            if msg.fan_title_id >= 6:
                raise NotImplementedError(
                    f'fan_title_id == {msg.fan_title_id}')
            fan_title = _fan_titles[msg.fan_title_id]

        if msg.zhuangjia:
            if msg.zimo:
                point_rong = None
                point_zimo_zhuangjia = None
                point_zimo_sanjia = msg.point_zimo_sanjia
            else:
                point_rong = msg.point_rong
                point_zimo_zhuangjia = None
                point_zimo_sanjia = None
        else:
            if msg.zimo:
                point_rong = None
                point_zimo_zhuangjia = msg.point_zimo_zhuangjia
                point_zimo_sanjia = msg.point_zimo_sanjia
            else:
                point_rong = msg.point_rong
                point_zimo_zhuangjia = None
                point_zimo_sanjia = None

        return Hule(seat=seat, zhuangjia=msg.zhuangjia, hand=hand,
                    ming_list=ming_list, hupai=hupai, lizhi=msg.lizhi,
                    zimo=msg.zimo, doras=doras, li_doras=li_doras, fu=msg.fu,
                    hupai_list=hupai_list, fan=msg.fan, fan_title=fan_title,
                    damanguan=msg.damanguan, point_rong=point_rong,
                    point_zimo_zhuangjia=point_zimo_zhuangjia,
                    point_zimo_sanjia=point_zimo_sanjia)

    try:
        hule_list = [decode_hule(h) for h in hule.hule_list]
        old_scores = [s for s in hule.old_scores]
        delta_scores = [s for s in hule.delta_scores]
        new_scores = [s for s in hule.new_scores]

        round_end_by_hule = RoundEndByHule(
            hule_list=hule_list, old_scores=old_scores,
            delta_scores=delta_scores, new_scores=new_scores)
        turn = Turn(round_end_by_hule)
        game_round.append_turn(turn)
    except Exception as e:
        raise RuntimeError(
            f'''Failed to decode the following Hule data:
{{'protobuf': hule, 'json': hule_json}}''')


def _on_no_tile(data: bytes, game_round: GameRound) -> None:
    no_tile = RecordNoTile()
    no_tile.ParseFromString(data)
    if no_tile.header != '.lq.RecordNoTile':
        print(no_tile.header)
        raise RuntimeError("Failed to parse `.lq.RecordNoTile'.")
    no_tile = no_tile.content
    no_tile_json = google.protobuf.json_format.MessageToDict(
        no_tile, including_default_value_fields=True,
        preserving_proto_field_name=True)

    no_tile_schema = {
        'title': '荒牌平局',
        'type': 'object',
        'required': [
            'liujumanguan',
            'players',
            'scores',
            'gameend'
        ],
        'properties': {
            'liujumanguan': {
                'title': '流し満貫フラグ',
                'description': 'false: 流し満貫ではない, true: 流し満貫である',
                'type': 'boolean'
            },
            'players': {
                'type': 'array',
                'minItems': 4,
                'maxItems': 4,
                'items': {
                    'type': 'object',
                    'required': [
                        'tingpai',
                        'hand',
                        'tingpai_list'
                    ],
                    'properties': {
                        'tingpai': {
                            'type': 'boolean'
                        },
                        'hand': {
                            'title': '聴牌時の手牌',
                            'description': '不聴の場合は空配列',
                            'type': 'array',
                            'maxItems': 13,
                            'items': _tile_schema,
                            'additionalItems': False
                        },
                        'tingpai_list': {
                            'type': 'array',
                            'items': _tingpai_schema,
                            'additionalItems': False
                        }
                    },
                    'additionalProperties': False
                },
                'additionalItems': False
            },
            'scores': {
                'type': 'array',
                'minItems': 1,
                'maxItems': 1,
                'items': {
                    'type': 'object',
                    'required': [
                        'seat',
                        'old_scores',
                        'delta_scores',
                        'hand',
                        'ming',
                        'doras',
                        'score'
                    ],
                    'properties': {
                        'seat': {
                            '$comment': '詳細不明．',
                            'const': 0
                        },
                        'old_scores': {
                            'title': '開局時の点数',
                            'type': 'array',
                            'minItems': 4,
                            'maxItems': 4,
                            'items': {
                                'type': 'integer'
                            },
                            'additionalItems': False
                        },
                        'delta_scores': {
                            'title': '点数収支',
                            'description': '全員聴牌または全員不聴で収支が無い場合は空配列．',
                            'type': 'array',
                            'maxItems': 4,
                            'items': {
                                'type': 'integer'
                            },
                            'additionalItems': False
                        },
                        'hand': {
                            '$comment': 'TODO: 詳細不明．',
                            'type': 'array',
                            'maxItems': 0
                        },
                        'ming': {
                            '$comment': 'TODO: 詳細不明．',
                            'type': 'array',
                            'maxItems': 0
                        },
                        'doras': {
                            '$comment': 'TODO: 詳細不明．',
                            'type': 'array',
                            'maxItems': 0
                        },
                        'score': {
                            '$comment': 'TODO: 詳細不明．',
                            'const': 0
                        }
                    },
                    'additionalProperties': False
                },
                'additionalItems': False
            },
            'gameend': {
                '$comment': 'TODO: 詳細不明．',
                'const': False
            }
        },
        'additionalProperties': False
    }

    try:
        jsonschema.validate(instance=no_tile_json, schema=no_tile_schema)
    except jsonschema.exceptions.ValidationError:
        raise RuntimeError(f'''Failed to validate the following NoTile data:
{{'protobuf': no_tile, 'json': no_tile_json}}''')

    try:
        liujumanguan = no_tile.liujumanguan

        player_results = []
        for i in range(len(no_tile.players)):
            player = no_tile.players[i]
            old_score = no_tile.scores[0].old_scores[i]

            if len(no_tile.scores[0].delta_scores) == 0:
                delta_score = 0
            elif len(no_tile.scores[0].delta_scores) == 4:
                delta_score = no_tile.scores[0].delta_scores[i]
            else:
                raise RuntimeError(f'delta_scores == {delta_scores}')

            tingpai = player.tingpai

            if tingpai:
                if len(player.hand) == 0:
                    raise RuntimeError(
                        f'tingpai == {tingpai}, hand == {player.hand}')
                hand = [Tile(code) for code in player.hand]
            else:
                if len(player.hand) != 0:
                    raise RuntimeError(
                        f'tingpai == {tingpai}, hand == {player.hand}')
                hand = None

            tingpai_list = [
                _decode_tingpai_info(tingpai) for tingpai in player.tingpai_list
            ]

            player_result = PlayerResultOnNoTile(
                tingpai=tingpai, hand=hand, tingpai_list=tingpai_list,
                old_score=old_score, delta_score=delta_score)
            player_results.append(player_result)

        no_tile = NoTile(liujumanguan=liujumanguan, player_results=player_results)
        turn = Turn(no_tile)
        game_round.append_turn(turn)
    except Exception as e:
        raise RuntimeError(
            f'''Failed to decode the following NoTile data:
{{'protobuf': no_tile, 'json': no_tile_json}}''')


def _on_liuju(data: bytes, game_round: GameRound) -> None:
    liuju = RecordLiuJu()
    liuju.ParseFromString(data)
    if liuju.header != '.lq.RecordLiuJu':
        raise RuntimeError("Failed to parse `.lq.RecordLiuJu'.")
    liuju = liuju.content
    liuju_json = google.protobuf.json_format.MessageToDict(
        liuju, including_default_value_fields=True,
        preserving_proto_field_name=True)

    liuju_schema = {
        'title': '途中流局',
        'oneOf': [
            {
                'title': '九種九牌',
                'type': 'object',
                'required': [
                    'type',
                    'seat',
                    'hand',
                    'allplayertiles'
                ],
                'properties': {
                    'type': {
                        'const': 1
                    },
                    'seat': _seat_schema,
                    'hand': {
                        'title': '九種九牌の場合の手牌',
                        'type': 'array',
                        'minItems': 14,
                        'maxItems': 14,
                        'items': _tile_schema,
                        'additionalItems': False
                    },
                    'allplayertiles': {
                        '$comment': 'TODO: 詳細不明．',
                        'type': 'array',
                        'maxItems': 0
                    }
                },
                'additionalProperties': False
            },
            {
                'title': '四風連打',
                'type': 'object',
                'required': [
                    'type',
                    'seat',
                    'hand',
                    'allplayertiles'
                ],
                'properties': {
                    'type': {
                        'const': 2
                    },
                    'seat': {
                        'const': 0
                    },
                    'hand': {
                        'type': 'array',
                        'maxItems': 0
                    },
                    'allplayertiles': {
                        '$comment': 'TODO: 詳細不明．',
                        'type': 'array',
                        'maxItems': 0
                    }
                },
                'additionalProperties': False
            }
        ]
    }

    try:
        jsonschema.validate(instance=liuju_json, schema=liuju_schema)
    except jsonschema.exceptions.ValidationError:
        raise RuntimeError(f'''Failed to validate the following Liuju data:
{{'protobuf': liuju, 'json': liuju_json}}''')

    try:
        if liuju.type == 1:
            seat = Seat(liuju.seat)
            hand = [Tile(code) for code in liuju.hand]
            kyushukyuhai = Kyushukyuhai(seat=seat, hand=hand)
            turn = Turn(turn=kyushukyuhai)
        elif liuju.type == 2:
            sifengzilianda = Sifengzilianda()
            turn = Turn(turn=sifengzilianda)

        game_round.append_turn(turn)
    except Exception as e:
        raise RuntimeError(
            f'''Failed to decode the following NoTile data:
{{'protobuf': liuju, 'json': liuju_json}}''')


_record_dispatcher = [
    (re.compile(b'^\n\x12\\.lq\\.RecordNewRound\x12', flags=re.DOTALL), _on_new_round),
    (re.compile(b'^\n\x12\\.lq\\.RecordDealTile\x12', flags=re.DOTALL), _on_deal_tile),
    (re.compile(b'^\n\x15\\.lq\\.RecordChiPengGang\x12', flags=re.DOTALL), _on_chi_peng_gang),
    (re.compile(b'^\n\x17\\.lq\\.RecordAnGangAddGang\x12', flags=re.DOTALL), _on_an_gang_add_gang),
    (re.compile(b'^\n\x15\\.lq\\.RecordDiscardTile\x12', flags=re.DOTALL), _on_discard_tile),
    (re.compile(b'^\n\x0e\\.lq\\.RecordHule\x12', flags=re.DOTALL), _on_hule),
    (re.compile(b'^\n\x10\\.lq\\.RecordNoTile\x12', flags=re.DOTALL), _on_no_tile),
    (re.compile(b'^\n\x0f\\.lq\\.RecordLiuJu\x12', flags=re.DOTALL), _on_liuju)
]


def on_fetch_game_record(request_message: WebSocketMessage,
                         response_message: WebSocketMessage) -> None:
    logging.info("Sniffering WebSocket messages from/to `.lq.Lobby.fetchGameRecord'.")

    request_string = request_message.content
    request = FetchGameRecordRequest()
    request.ParseFromString(request_string[32:])
    #print(request)

    response_string = response_message.content
    #print(binascii.hexlify(response_string))
    #with open('fetch_game_record.response', 'wb') as f:
    #    f.write(response_string)
    response = FetchGameRecordResponse()
    response.ParseFromString(response_string[3:])
    response = response.content

    game_summary_schema = {
        'type': 'object',
        'required': [
            'uuid',
            'start_time',
            'end_time',
            'config',
            'accounts',
            'result'
        ],
        'properties': {
            'uuid': {
                'type': 'string'
            },
            'start_time': {
                'type': 'integer',
                'minimum': 0
            },
            'end_time': {
                'type': 'integer',
                'minimum': 0
            },
            'config': {
                'type': 'object',
                'required': [
                    'category',
                    'mode',
                    'meta'
                ],
                'properties': {
                    'category': {
                        'description': '1: 友人戦, 2: 段位戦',
                        'type': 'integer',
                        'minimum': 0
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
                                '$commend': 'TODO: 詳細不明',
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
            'accounts': {
                'title': '各席のアカウント情報',
                'description': 'CPU を入れた場合，要素数が4未満になる．',
                'type': 'array',
                'minItems': 1,
                'maxItems': 4,
                'items': {
                    'type': 'object',
                    'required': [
                        'account_id',
                        'seat',
                        'nickname',
                        'avatar_id',
                        'character',
                        'title',
                        'level',
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
                        'seat': _seat_schema,
                        'nickname': {
                            'type': 'string'
                        },
                        'avatar_id': {
                            'type': 'integer',
                            'minimum': 0
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
                                    'minimum': 0
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
                        'title': {
                            'title': '称号',
                            'type': 'integer',
                            'minimum': 0
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
                            'miniumumItems': 1,
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
            'result': {
                'type': 'object',
                'required': [
                    'players'
                ],
                'properties': {
                    'players': {
                        'type': 'array',
                        'minItems': 4,
                        'maxItems': 4,
                        'items': {
                            'type': 'object',
                            'required': [
                                'seat',
                                'total_score',
                                'base_score',
                                'part_point_2',
                                'grading_point',
                                'coin'
                            ],
                            'properties': {
                                'seat': _seat_schema,
                                'total_score': {
                                    'title': '順位ウマを含めた最終点数',
                                    'description': '0の場合はキー自体が存在しない．',
                                    'type': 'integer',
                                },
                                'base_score': {
                                    'title': '順位ウマを除いた最終点数',
                                    'description': '0の場合はキー自体が存在しない．',
                                    'type': 'integer'
                                },
                                'part_point_2': {
                                    'const': 0
                                },
                                'grading_point': {
                                    'title': '段位ポイントの増減',
                                    'description': '友人戦ではキー自体が存在しない．',
                                    'type': 'integer'
                                },
                                'coin': {
                                    'title': 'コインの増減',
                                    'description': '友人戦ではキー自体が存在しない．',
                                    'type': 'integer'
                                }
                            },
                            'additionalProperties': False
                        },
                        'additionalItems': False
                    }
                },
                'additionalProperties': False
            }
        },
        'additionalProperties': False
    }

    def decode_account_level(msg: google.protobuf.message) -> AccountLevel:
        id = msg.id
        if id // 10000 not in [1, 2]:
            raise NotImplementedError(f'id == {id}')

        title_id = id % 10000
        if title_id // 100 == 1:
            title = '初心'
        elif title_id // 100 == 2:
            title = '雀士'
        elif title_id // 100 == 3:
            title = '雀傑'
        elif title_id // 100 == 4:
            title = '雀豪'
        elif title_id // 100 == 5:
            title = '雀聖'
        elif title_id // 100 == 6:
            title = '魂天'
        else:
            raise NotImplementedError(f'id == {id}')

        return AccountLevel(title=title, level=title_id % 100,
                            grading_point=msg.grading_point)

    game_summary = response.summary
    game_summary_json = google.protobuf.json_format.MessageToDict(
        game_summary, including_default_value_fields=True,
        preserving_proto_field_name=True)
    try:
        jsonschema.validate(instance=game_summary_json, schema=game_summary_schema)
    except jsonschema.exceptions.ValidationError:
        raise RuntimeError(f'''Failed to validate the game summary data:
{game_summary}''')

    start_time = datetime.datetime.fromtimestamp(game_summary.start_time)

    game_record_placeholder = GameRecordPlaceholder(
        uuid=game_summary.uuid, start_time=start_time)

    end_time = datetime.datetime.fromtimestamp(game_summary.end_time)

    if game_summary.config.meta.mode_id == 2:
        mode = '段位戦・銅の間・四人東風戦'
    elif game_summary.config.meta.mode_id == 6:
        mode = '段位戦・銀の間・四人半荘戦'
    elif game_summary.config.meta.mode_id == 8:
        mode = '段位戦・金の間・四人東風戦'
    elif game_summary.config.meta.mode_id == 9:
        mode = '段位戦・金の間・四人半荘戦'
    elif game_summary.config.meta.mode_id == 11:
        mode = '段位戦・玉の間・四人東風戦'
    elif game_summary.config.meta.mode_id == 12:
        mode = '段位戦・玉の間・四人半荘戦'
    elif game_summary.config.meta.mode_id == 16:
        mode = '段位戦・王座の間・四人半荘戦'
    elif game_summary.config.meta.mode_id == 21:
        mode = '段位戦・金の間・三人東風戦'
    elif game_summary.config.meta.mode_id == 22:
        mode = '段位戦・金の間・三人半荘戦'
    elif game_summary.config.meta.mode_id == 23:
        mode = '段位戦・玉の間・三人東風戦'
    elif game_summary.config.meta.mode_id == 24:
        mode = '段位戦・玉の間・三人半荘戦'
    elif game_summary.config.meta.mode_id == 26:
        mode = '段位戦・王座の間・三人半荘戦'
    else:
        raise NotImplementedError(
            f'mode_id == {game_summary.config.meta.mode_id}')

    results = [None, None, None, None]
    for player_result in game_summary.result.players:
        seat = player_result.seat
        base_score = player_result.base_score
        total_score = player_result.total_score
        delta_grading_point = player_result.grading_point
        delta_coin = player_result.coin
        results[seat] = (base_score, total_score, delta_grading_point,
                         delta_coin)
    for i in range(len(results)):
        if results[i] is None:
            raise RuntimeError(f'index == {i}')

    account_list = [None, None, None, None]
    for i in range(len(game_summary.accounts)):
        account_id = game_summary.accounts[i].account_id
        seat = game_summary.accounts[i].seat
        account_nickname = game_summary.accounts[i].nickname
        account_level4 = decode_account_level(game_summary.accounts[i].level)
        account_level3 = decode_account_level(game_summary.accounts[i].level3)
        base_score, total_score, delta_grading_point, delta_coin = results[seat]
        account = Account(id=account_id, nickname=account_nickname,
                          level4=account_level4, level3=account_level3,
                          final_base_score=base_score,
                          final_total_score=total_score,
                          delta_grading_point=delta_grading_point,
                          delta_coin=delta_coin)
        account_list[seat] = account
    for i in range(len(account_list)):
        if account_list[i] is None:
            raise RuntimeError(f'index == {i}')

    game_record = GameRecord(
        placeholder=game_record_placeholder, end_time=end_time, mode=mode,
        account_list=account_list)

    if response.detail.header != '.lq.GameDetailRecords':
        print(response.detail.header)
        raise RuntimeError(
            "Unknown data in response from `.lq.Lobby.fetchGameRecord'.")
    data = response.detail.data
    game_detail_records = GameDetailRecords()
    game_detail_records.ParseFromString(data)

    game_round = None
    for record in game_detail_records.records:
        default = True
        for pattern, target in _record_dispatcher:
            if pattern.search(record):
                if target is _on_new_round:
                    if game_round is not None:
                        game_record.append_game_round(game_round)
                    game_round = target(record)
                else:
                    try:
                        target(record, game_round)
                    except Exception as e:
                        raise RuntimeError(
                            f'{game_round.chang}{game_round.ju + 1}局{game_round.ben}本場')
                default = False
                break
        if default:
            raise RuntimeError(
                f"An unknown record in `.lq.Lobby.fetchGameRecord': {record}")
    if game_round is None:
        raise RuntimeError('No game round is found.')
    game_record.append_game_round(game_round)
