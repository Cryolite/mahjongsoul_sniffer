#!/usr/bin/env python3

import re
import datetime
import logging
import json
from typing import (Optional,)
import jsonschema
import jsonschema.exceptions
import google.protobuf.json_format
from mahjongsoul_sniffer.mahjongsoul_pb2 \
    import (Wrapper, ResGameRecord, GameDetailRecords, RecordNewRound,
            RecordDealTile, RecordDiscardTile, RecordChiPengGang,
            RecordAnGangAddGang, RecordHule, RecordNoTile, RecordLiuJu)


_SEAT_SCHEMA = {
    'title': '座席',
    'description': '0: 起家, 1: 起家の下家, 2: 起家の対面, 3: 起家の上家',
    'enum': [
        0,
        1,
        2,
        3
    ]
}


_SUMMARY_SCHEMA = {
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
            'title': 'ゲーム UUID',
            'type': 'string'
        },
        'start_time': {
            'title': '開始時間',
            'description': 'ゲーム開始時間のタイムスタンプ',
            'type': 'integer',
            'minimum': 0
        },
        'end_time': {
            'title': '終了時間',
            'description': 'ゲーム終了時間のタイムスタンプ',
            'type': 'integer',
            'minimum': 0
        },
        'config': {
            'title': 'ゲームのモードおよびルール設定',
            'type': 'object',
            'required': [
                'category',
                'mode',
                'meta'
            ],
            'properties': {
                'category': {
                    'title': 'ゲームカテゴリ',
                    'description': '1: 友人戦, 2: 段位戦',
                    'enum': [
                        1,
                        2
                    ]
                },
                'mode': {
                    'title': 'ゲームモード',
                    'type': 'object',
                    'required': [
                        'mode',
                        'ai',
                        'extendinfo',
                        'detail_rule'
                    ],
                    'properties': {
                        'mode': {
                            'title': 'ゲームモード',
                            'description': '1: 東風戦, 2: 半荘戦, 4: 一局戦',
                            'enum': [
                                1,
                                2,
                                4
                            ]
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
                            'title': 'ゲームルール詳細',
                            '$comment': 'TODO: 要調査, 段位戦などルールのプリセットがある場合は'
                                        'meta.mode_id が参照され，ここはすべてデフォルト値？',
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
                            'title': '友人戦 ID',
                            'description': '友人戦でない場合は0．',
                            'type': 'integer',
                            'minimum': 0
                        },
                        'mode_id': {
                            'title': 'ゲームプリセット',
                            'description': '2: 段位戦・銅の間・四人東風戦, '
                                           '6: 段位戦・銀の間・四人半荘戦, '
                                           '8: 段位戦・金の間・四人東風戦, '
                                           '9: 段位戦・金の間・四人半荘戦, '
                                           '11: 段位戦・玉の間・四人東風戦, '
                                           '12: 段位戦・玉の間・四人半荘戦, '
                                           '15: 段位戦・王座の間・四人東風戦, '
                                           '16: 段位戦・王座の間・四人半荘戦, '
                                           '21: 段位戦・金の間・三人東風戦, '
                                           '22: 段位戦・金の間・三人半荘戦, '
                                           '23: 段位戦・玉の間・三人東風戦, '
                                           '24: 段位戦・玉の間・三人半荘戦, '
                                           '26: 段位戦・王座の間・三人半荘戦',
                            'enum': [
                                2,
                                6,
                                8,
                                9,
                                11,
                                12,
                                15,
                                16,
                                21,
                                22,
                                23,
                                24,
                                26
                            ]
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
                        'title': 'アカウント ID',
                        'type': 'integer',
                        'minimum': 0
                    },
                    'seat': _SEAT_SCHEMA,
                    'nickname': {
                        'title': 'ユーザー名',
                        'type': 'string'
                    },
                    'avatar_id': {
                        'title': 'アバター ID',
                        'type': 'integer',
                        'minimum': 0
                    },
                    'character': {
                        'title': 'キャラクタ情報',
                        'type': 'object',
                        'required': [
                            'charid',
                            'level',
                            'exp',
                            'views',
                            'skin',
                            'is_upgraded',
                            'extra_emoji'
                        ],
                        'properties': {
                            'charid': {
                                'title': 'キャラクタ ID',
                                'type': 'integer',
                                'minimum': 0
                            },
                            'level': {
                                'title': '絆レベル？',
                                'type': 'integer',
                                'minimum': 0
                            },
                            'exp': {
                                'title': '絆ポイント？',
                                'type': 'integer',
                                'minimum': 0
                            },
                            'views': {
                                '$comment': 'TODO: 詳細不明',
                                'type': 'array',
                                'maxItems': 0,
                                'additionalItems': False
                            },
                            'skin': {
                                '$comment': 'TODO: 詳細不明',
                                'type': 'integer',
                                'minimum': 0
                            },
                            'is_upgraded': {
                                'title': '契約済みフラグ',
                                'description': 'false: キャラクタと契約してない, true: キャラクタと契約済み',
                                'type': 'boolean'
                            },
                            'extra_emoji': {
                                'title': '追加スタンプ？',
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
                        'description': '0: 称号なし, '
                                       '600002: 原初の火, '
                                       '600003: (詳細不明), '
                                       '600004: 最初の雀聖, '
                                       '600005: 魂の契約者1, '
                                       '600006: 魂の契約者2, '
                                       '600007: 魂の契約者3, '
                                       '600008: 魂の啓発者1, '
                                       '600009: 魂の啓発者2, '
                                       '600010: 魂の啓発者3, '
                                       '600011: 魂の創造者1, '
                                       '600012: 魂の創造者2, '
                                       '600013: 魂の創造者3, '
                                       '600014: 魂の超越者, '
                                       '600015: キャットフード商人, '
                                       '600016: 最初の魂天, '
                                       '600017: 公認プレイヤー, '
                                       '600018: (詳細不明), '
                                       '600019: (詳細不明), '
                                       '600020: (詳細不明), '
                                       '600021: にゃん国の守護者, '
                                       '600022: (詳細不明), '
                                       '600026: 公認プレイヤーG, '
                                       '600027: (詳細不明), '
                                       '600028: 1st Season 挑戦者, '
                                       '600029: インターハイ王者, '
                                       '600031: 成長の旅, '
                                       '600032: 連勝の道, '
                                       '600037: (詳細不明), '
                                       '600038: (詳細不明), '
                                       '600044: 花より団子 (にじさんじ麻雀杯 花鳥風月戦 優勝賞品), '
                                       '600045: (詳細不明), '
                                       '600046: (詳細不明)',
                        'enum': [
                            0,
                            600002,
                            600003,
                            600004,
                            600005,
                            600006,
                            600007,
                            600008,
                            600009,
                            600010,
                            600011,
                            600012,
                            600013,
                            600014,
                            600015,
                            600016,
                            600017,
                            600018,
                            600019,
                            600020,
                            600021,
                            600022,
                            600026,
                            600027,
                            600028,
                            600029,
                            600031,
                            600032,
                            600037,
                            600038,
                            600044,
                            600045,
                            600046,
                        ]
                    },
                    'level': {
                        'title': '四人戦段位',
                        'type': 'object',
                        'required': [
                            'id',
                            'score'
                        ],
                        'properties': {
                            'id': {
                                'title': '四人戦段位 ID',
                                'description': '1010X: 初心, '
                                               '1020X: 雀士, '
                                               '1030X: 雀傑, '
                                               '1040X: 雀豪, '
                                               '1050X: 雀聖, '
                                               '10601: 魂天, '
                                               '1070X: 魂天 (2021/08/26 魂珠導入以降)',
                                'enum': [
                                    10101,
                                    10102,
                                    10103,
                                    10201,
                                    10202,
                                    10203,
                                    10301,
                                    10302,
                                    10303,
                                    10401,
                                    10402,
                                    10403,
                                    10501,
                                    10502,
                                    10503,
                                    10601,
                                    10701,
                                    10702,
                                    10703,
                                ]
                            },
                            'score': {
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
                            'score'
                        ],
                        'properties': {
                            'id': {
                                'title': '三人戦段位 ID',
                                'description': '2010X: 初心, '
                                               '2020X: 雀士, '
                                               '2030X: 雀傑, '
                                               '2040X: 雀豪, '
                                               '2050X: 雀聖, '
                                               '20601: 魂天, '
                                               '2070X: 魂天 (2021/08/26 魂珠導入以降)',
                                'enum': [
                                    20101,
                                    20102,
                                    20103,
                                    20201,
                                    20202,
                                    20203,
                                    20301,
                                    20302,
                                    20303,
                                    20401,
                                    20402,
                                    20403,
                                    20501,
                                    20502,
                                    20503,
                                    20601,
                                    20701,
                                    20702,
                                ]
                            },
                            'score': {
                                'title': '三人戦昇段ポイント',
                                'type': 'integer',
                                'minimum': 0
                            }
                        },
                        'additionalProperties': False
                    },
                    'avatar_frame': {
                        'title': 'アイコンフレーム',
                        'description': '0: 無し, '
                                       '305500: 若葉, '
                                       '305510: 「四象戦 -夏の陣-」優勝賞品？, '
                                       '305511: (詳細不明), '
                                       '305512: 「四象戦 -秋の陣-」優勝賞品？, '
                                       '305514: (詳細不明), '
                                       '305515: 「四象戦 -冬の陣-」優勝賞品？, '
                                       '305516: (詳細不明), '
                                       '305517: (詳細不明), '
                                       '305518: 「2021雀魂四象戦 ～春の陣～」優勝賞品？, '
                                       '305519: 「2021雀魂四象戦 ～夏の陣～」優勝賞品？, '
                                       '305520: 試練の強者 (試練の道 1st Season ランキング11～100位報酬), '
                                       '305521: 試練の賢者 (試練の道 1st Season ランキング2～10位報酬), '
                                       '305522: 試練の覇者 (試練の道 1st Season ランキング1位報酬), '
                                       '305523: 猫ちゃん軍団長, '
                                       '305524: (詳細不明), '
                                       '305525: 「2021雀魂双聖戦 一回戦」優勝賞品？',
                        'enum': [
                            0,
                            305500,
                            305510,
                            305511,
                            305512,
                            305514,
                            305515,
                            305516,
                            305517,
                            305518,
                            305519,
                            305520,
                            305521,
                            305522,
                            305523,
                            305524,
                            305525
                        ]
                    },
                    'verified': {
                        'title': '公認プレイヤーフラグ',
                        'description': '0: 一般アカウント, '
                                       '1: にくきゅうま～く付アカウント, '
                                       '2: プロ雀士認証マーク',
                        'enum': [
                            0,
                            1,
                            2
                        ]
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
            'title': '対戦結果',
            'type': 'object',
            'required': [
                'players'
            ],
            'properties': {
                'players': {
                    'title': '各プレイヤの対戦結果',
                    'type': 'array',
                    'minItems': 3,
                    'maxItems': 4,
                    'items': {
                        'type': 'object',
                        'required': [
                            'seat',
                            'total_point',
                            'part_point_1',
                            'part_point_2',
                            'grading_score',
                            'gold'
                        ],
                        'properties': {
                            'seat': _SEAT_SCHEMA,
                            'total_point': {
                                'title': '順位ウマを含めた最終点数',
                                'type': 'integer'
                            },
                            'part_point_1': {
                                'title': '順位ウマを除いた最終点数',
                                'type': 'integer'
                            },
                            'part_point_2': {
                                '$comment': 'TODO: 詳細不明',
                                'const': 0
                            },
                            'grading_score': {
                                'title': '段位ポイントの増減',
                                'description': '友人戦では常に0．',
                                'type': 'integer'
                            },
                            'gold': {
                                'title': 'コインの増減',
                                'description': '友人戦では常に0．',
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


_GAME_RECORD_SCHEMA = {
    'type': 'object',
    'required': [
        'head',
        'data',
        'data_url'
    ],
    'properties': {
        'head': _SUMMARY_SCHEMA,
        'data': {
            'type': 'string'
        },
        'data_url': {
            '$comment': 'TODO: 詳細不明',
            'const': ''
        }
    },
    'additionalProperties': False
}


_TILE_SCHEMA = {
    'title': '牌種',
    'enum': [
        '0m',
        '1m',
        '2m',
        '3m',
        '4m',
        '5m',
        '6m',
        '7m',
        '8m',
        '9m',
        '0p',
        '1p',
        '2p',
        '3p',
        '4p',
        '5p',
        '6p',
        '7p',
        '8p',
        '9p',
        '0s',
        '1s',
        '2s',
        '3s',
        '4s',
        '5s',
        '6s',
        '7s',
        '8s',
        '9s',
        '1z',
        '2z',
        '3z',
        '4z',
        '5z',
        '6z',
        '7z',
    ]
}


_TINGPAI_SCHEMA = {
    'title': '聴牌情報',
    'required': [
        'tile',
        'haveyi',
        'yiman',
        'count',
        'fu',
        'biao_dora_count',
        'yiman_zimo',
        'count_zimo',
        'fu_zimo'
    ],
    'properties': {
        'tile': _TILE_SCHEMA,
        'haveyi': {
            'title': '役の有無',
            'description': 'false: 役無し, true: 和了に必要な一翻がある',
            'type': 'boolean'
        },
        'yiman': {
            'title': '出上がり役満聴牌',
            'description': 'false: 出上がり役満聴牌ではない, true: 出上がり役満聴牌である',
            'type': 'boolean'
        },
        'count': {
            'title': '栄和の場合のドラを除いた確定翻数',
            'type': 'integer',
            'minimum': 0
        },
        'fu': {
            'title': '栄和の場合の符',
            'type': 'integer',
            'minimum': 25
        },
        'biao_dora_count': {
            'title': '確定ドラ数',
            'type': 'integer',
            'minimum': 0
        },
        'yiman_zimo': {
            'title': '自模り役満聴牌',
            'description': 'false: 自模り役満聴牌ではない, true: 自模り役満聴牌である',
            'type': 'boolean'
        },
        'count_zimo': {
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


_ZIMO_OPTION_SCHEMA = {
    'title': '自摸時選択肢',
    'description': '嶺上牌を含む自摸の直後，またはチー・ポンの直後に可能な操作の選択肢．',
    'oneOf': [
        {
            'title': '打牌',
            'type': 'object',
            'required': [
                'type',
                'combination',
                'change_tiles',
                'change_tile_states'
            ],
            'properties': {
                'type': {
                    'const': 1
                },
                'combination': {
                    '$comment': 'TODO: 鳴いた時の打牌時に存在するが詳細不明．食い替えで打牌が禁止される牌か？',
                    'type': 'array',
                    'items': _TILE_SCHEMA,
                    'additionalItems': False
                },
                'change_tiles': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                },
                'change_tile_states': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
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
                'combination',
                'change_tiles',
                'change_tile_states'
            ],
            'properties': {
                'type': {
                    'const': 4
                },
                'combination': {
                    'type': 'array',
                    'minItems': 1,
                    'maxItems': 3,
                    'items': {
                        'description': '暗槓の対象牌4つを "|" で区切った文字列．',
                        '$comment': '"5m|5m|5m|0m" の類は自摸牌が赤5の時かつその時に限る？',
                        'enum': [
                            '1m|1m|1m|1m',
                            '2m|2m|2m|2m',
                            '3m|3m|3m|3m',
                            '4m|4m|4m|4m',
                            '0m|5m|5m|5m',
                            '5m|5m|5m|0m',
                            '6m|6m|6m|6m',
                            '7m|7m|7m|7m',
                            '8m|8m|8m|8m',
                            '9m|9m|9m|9m',
                            '1p|1p|1p|1p',
                            '2p|2p|2p|2p',
                            '3p|3p|3p|3p',
                            '4p|4p|4p|4p',
                            '0p|5p|5p|5p',
                            '5p|5p|5p|0p',
                            '6p|6p|6p|6p',
                            '7p|7p|7p|7p',
                            '8p|8p|8p|8p',
                            '9p|9p|9p|9p',
                            '1s|1s|1s|1s',
                            '2s|2s|2s|2s',
                            '3s|3s|3s|3s',
                            '4s|4s|4s|4s',
                            '0s|5s|5s|5s',
                            '5s|5s|5s|0s',
                            '6s|6s|6s|6s',
                            '7s|7s|7s|7s',
                            '8s|8s|8s|8s',
                            '9s|9s|9s|9s',
                            '1z|1z|1z|1z',
                            '2z|2z|2z|2z',
                            '3z|3z|3z|3z',
                            '4z|4z|4z|4z',
                            '5z|5z|5z|5z',
                            '6z|6z|6z|6z',
                            '7z|7z|7z|7z'
                        ]
                    },
                    'additionalItems': False
                },
                'change_tiles': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                },
                'change_tile_states': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
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
                'combination',
                'change_tiles',
                'change_tile_states'
            ],
            'properties': {
                'type': {
                    'const': 6
                },
                'combination': {
                    'type': 'array',
                    'minItems': 1,
                    'maxItems': 3,
                    'items': {
                        'description': '加槓の対象牌4つを "|" で区切った文字列．',
                        'enum': [
                            '1m|1m|1m|1m',
                            '2m|2m|2m|2m',
                            '3m|3m|3m|3m',
                            '4m|4m|4m|4m',
                            '0m|5m|5m|5m',
                            '6m|6m|6m|6m',
                            '7m|7m|7m|7m',
                            '8m|8m|8m|8m',
                            '9m|9m|9m|9m',
                            '1p|1p|1p|1p',
                            '2p|2p|2p|2p',
                            '3p|3p|3p|3p',
                            '4p|4p|4p|4p',
                            '0p|5p|5p|5p',
                            '6p|6p|6p|6p',
                            '7p|7p|7p|7p',
                            '8p|8p|8p|8p',
                            '9p|9p|9p|9p',
                            '1s|1s|1s|1s',
                            '2s|2s|2s|2s',
                            '3s|3s|3s|3s',
                            '4s|4s|4s|4s',
                            '0s|5s|5s|5s',
                            '6s|6s|6s|6s',
                            '7s|7s|7s|7s',
                            '8s|8s|8s|8s',
                            '9s|9s|9s|9s',
                            '1z|1z|1z|1z',
                            '2z|2z|2z|2z',
                            '3z|3z|3z|3z',
                            '4z|4z|4z|4z',
                            '5z|5z|5z|5z',
                            '6z|6z|6z|6z',
                            '7z|7z|7z|7z'
                        ]
                    },
                    'additionalItems': False
                },
                'change_tiles': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                },
                'change_tile_states': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
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
                'combination',
                'change_tiles',
                'change_tile_states'
            ],
            'properties': {
                'type': {
                    'const': 7
                },
                'combination': {
                    'description': '立直のために打牌する牌，つまり立直宣言牌になる牌の候補．',
                    'type': 'array',
                    'minItems': 1,
                    'items': _TILE_SCHEMA,
                    'additionalItems': False
                },
                'change_tiles': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                },
                'change_tile_states': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
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
                'combination',
                'change_tiles',
                'change_tile_states'
            ],
            'properties': {
                'type': {
                    'const': 8
                },
                'combination': {
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                },
                'change_tiles': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                },
                'change_tile_states': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                }
            },
            'additionalProperties': False
        },
        {
            'title': '九種九牌',
            'type': 'object',
            'required': [
                'type',
                'combination',
                'change_tiles',
                'change_tile_states'
            ],
            'properties': {
                'type': {
                    'const': 10
                },
                'combination': {
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                },
                'change_tiles': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                },
                'change_tile_states': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                }
            },
            'additionalProperties': False
        }
    ]
}


_ZIMO_OPTION_PRESENCE_SCHEMA = {
    'title': '自摸時選択肢提示',
    '$comment': '親の配牌直後，嶺上牌を含む自摸直後，およびチー・ポンの直後に可能な選択肢の提示．',
    'type': 'object',
    'required': [
        'seat',
        'operation_list',
        'time_add',
        'time_fixed'
    ],
    'properties': {
        'seat': _SEAT_SCHEMA,
        'operation_list': {
            '$comment': '立直宣言者は打牌が自動になるので空配列になる場合がある．',
            'type': 'array',
            'items': _ZIMO_OPTION_SCHEMA,
            'additionalItems': False
        },
        'time_add': {
            'title': '追加考慮時間（ミリ秒）',
            'type': 'integer',
            'minimum': 0
        },
        'time_fixed': {
            'title': '基本考慮時間（ミリ秒）',
            'type': 'integer',
            'minimum': 0
        }
    },
    'additionalProperties': False
}


_NEW_ROUND_SCHEMA = {
    'title': '開局',
    'type': 'object',
    'required': [
        'chang',
        'ju',
        'ben',
        'dora',
        'scores',
        'liqibang',
        'tiles0',
        'tiles1',
        'tiles2',
        'tiles3',
        'tingpai',
        'operation',
        'md5',
        'paishan',
        'left_tile_count',
        'doras',
        'opens',
        'operations'
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
            'minItems': 3,
            'maxItems': 4,
            'items': {
                'type': 'integer'
            },
            'additionalItems': False
        },
        'liqibang': {
            'title': '供託本数',
            'type': 'integer',
            'minimum': 0
        },
        'tiles0': {
            'title': '起家の配牌',
            'type': 'array',
            'minItems': 13,
            'maxItems': 14,
            'items': _TILE_SCHEMA,
            'additionalItems': False
        },
        'tiles1': {
            'title': '起家の下家の配牌',
            'type': 'array',
            'minItems': 13,
            'maxItems': 14,
            'items': _TILE_SCHEMA,
            'additionalItems': False
        },
        'tiles2': {
            'title': '起家の対面の配牌',
            'type': 'array',
            'minItems': 13,
            'maxItems': 14,
            'items': _TILE_SCHEMA,
            'additionalItems': False
        },
        'tiles3': {
            'title': '起家の上家の配牌',
            'type': 'array',
            'minItems': 13,
            'maxItems': 14,
            'items': _TILE_SCHEMA,
            'additionalItems': False
        },
        'tingpai': {
            'title': '配牌時の各家の聴牌情報',
            'type': 'array',
            'maxItems': 4,
            'items': {
                'type': 'object',
                'required': [
                    'seat',
                    'tingpais1'
                ],
                'properties': {
                    'seat': _SEAT_SCHEMA,
                    'tingpais1': {
                        'type': 'array',
                        'minItems': 1,
                        'items': _TINGPAI_SCHEMA,
                        'additionalItems': False
                    }
                },
                'additionalProperties': False
            },
            'additionalItems': False
        },
        'operation': _ZIMO_OPTION_PRESENCE_SCHEMA,
        'md5': {
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
            'items': _TILE_SCHEMA,
            'additionalItems': False
        },
        'opens': {
            '$comment': 'TODO: 詳細不明．',
            'type': 'array',
            'minItems': 3,
            'maxItems': 4,
            'items': {
                'type': 'object',
                'required': [
                    'seat',
                    'tiles',
                    'count'
                ],
                'properties': {
                    'seat': _SEAT_SCHEMA,
                    'tiles': {
                        'type': 'array',
                        'maxItems': 0,
                        'additionalProperties': False
                    },
                    'count': {
                        'type': 'array',
                        'maxItems': 0,
                        'additionalProperties': False
                    }
                },
                'additionalProperties': False
            },
            'additionalItems': False
        },
        'operations': {
            '$comment': 'TODO: 詳細不明．',
            'type': 'array',
            'maxItems': 0,
            'additionalItems': False
        }
    },
    'additionalProperties': False
}


_PREV_LIZHI_SCHEMA = {
    'title': '直前の立直に対する立直棒演出',
    'type': 'object',
    'required': [
        'seat',
        'score',
        'liqibang',
        'failed'
    ],
    'properties': {
        'seat': _SEAT_SCHEMA,
        'score': {
            'type': 'integer',
            'minimum': 0
        },
        'liqibang': {
            '$comment': '立直棒の種類か？',
            'type': 'integer',
            'minimum': 0
        },
        'failed': {
            '$comment': 'TODO: 詳細不明．',
            'const': False
        }
    },
    'additionalProperties': False
}


_ZHENTING_SCHEMA = {
    'title': '振聴フラグ',
    'description': 'false: 振聴ではない, true: 振聴である',
    'type': 'array',
    'minItems': 3,
    'maxItems': 4,
    'items': {
        'type': 'boolean'
    },
    'additionalItems': False
}


_DEAL_TILE_SCHEMA = {
    'title': '自摸',
    'type': 'object',
    'required': [
        'seat',
        'tile',
        'left_tile_count',
        'doras',
        'zhenting',
        'operation',
        'tile_state'
    ],
    'properties': {
        'seat': _SEAT_SCHEMA,
        'tile': _TILE_SCHEMA,
        'left_tile_count': {
            'title': '残り自摸牌数',
            'type': 'integer',
            'minimum': 0
        },
        'liqi': _PREV_LIZHI_SCHEMA,
        'doras': {
            'title': 'ドラ',
            'description': '嶺上牌を自摸った際に新ドラを表示する必要があるために存在する．新旧の全ドラを含む．',
            'type': 'array',
            'items': _TILE_SCHEMA,
            'additionalItems': False
        },
        'zhenting': _ZHENTING_SCHEMA,
        'operation': _ZIMO_OPTION_PRESENCE_SCHEMA,
        'tile_state': {
            '$comment': '詳細不明．',
            'const': 0
        }
    },
    'additionalProperties': False
}


_CHI_OPTION_SCHEMA = {
    'title': 'チーの選択肢',
    'type': 'object',
    'required': [
        'type',
        'combination',
        'change_tiles',
        'change_tile_states'
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
                'enum': [
                    '1m|2m',
                    '1m|3m',
                    '2m|3m',
                    '2m|4m',
                    '3m|4m',
                    '3m|0m',
                    '3m|5m',
                    '4m|0m',
                    '4m|5m',
                    '4m|6m',
                    '0m|6m',
                    '0m|7m',
                    '5m|6m',
                    '5m|7m',
                    '6m|7m',
                    '6m|8m',
                    '7m|8m',
                    '7m|9m',
                    '8m|9m',
                    '1p|2p',
                    '1p|3p',
                    '2p|3p',
                    '2p|4p',
                    '3p|4p',
                    '3p|0p',
                    '3p|5p',
                    '4p|0p',
                    '4p|5p',
                    '4p|6p',
                    '0p|6p',
                    '0p|7p',
                    '5p|6p',
                    '5p|7p',
                    '6p|7p',
                    '6p|8p',
                    '7p|8p',
                    '7p|9p',
                    '8p|9p',
                    '1s|2s',
                    '1s|3s',
                    '2s|3s',
                    '2s|4s',
                    '3s|4s',
                    '3s|0s',
                    '3s|5s',
                    '4s|0s',
                    '4s|5s',
                    '4s|6s',
                    '0s|6s',
                    '0s|7s',
                    '5s|6s',
                    '5s|7s',
                    '6s|7s',
                    '6s|8s',
                    '7s|8s',
                    '7s|9s',
                    '8s|9s'
                ]
            },
            'additionalItems': False
        },
        'change_tiles': {
            '$comment': 'TODO: 詳細不明．',
            'type': 'array',
            'maxItems': 0,
            'additionalItems': False
        },
        'change_tile_states': {
            '$comment': 'TODO: 詳細不明．',
            'type': 'array',
            'maxItems': 0,
            'additionalItems': False
        }
    },
    'additionalProperties': False
}


_PENG_OPTION_SCHEMA = {
    'title': 'ポンの選択肢',
    'type': 'object',
    'required': [
        'type',
        'combination',
        'change_tiles',
        'change_tile_states'
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
                'enum': [
                    '1m|1m',
                    '2m|2m',
                    '3m|3m',
                    '4m|4m',
                    '0m|5m',
                    '5m|5m',
                    '6m|6m',
                    '7m|7m',
                    '8m|8m',
                    '9m|9m',
                    '1p|1p',
                    '2p|2p',
                    '3p|3p',
                    '4p|4p',
                    '0p|5p',
                    '5p|5p',
                    '6p|6p',
                    '7p|7p',
                    '8p|8p',
                    '9p|9p',
                    '1s|1s',
                    '2s|2s',
                    '3s|3s',
                    '4s|4s',
                    '0s|5s',
                    '5s|5s',
                    '6s|6s',
                    '7s|7s',
                    '8s|8s',
                    '9s|9s',
                    '1z|1z',
                    '2z|2z',
                    '3z|3z',
                    '4z|4z',
                    '5z|5z',
                    '6z|6z',
                    '7z|7z'
                ]
            },
            'additionalItems': False
        },
        'change_tiles': {
            '$comment': 'TODO: 詳細不明．',
            'type': 'array',
            'maxItems': 0,
            'additionalItems': False
        },
        'change_tile_states': {
            '$comment': 'TODO: 詳細不明．',
            'type': 'array',
            'maxItems': 0,
            'additionalItems': False
        }
    },
    'additionalProperties': False
}


_DAMINGGANG_OPTION_SCHEMA = {
    'title': '大明槓の選択肢',
    'type': 'object',
    'required': [
        'type',
        'combination',
        'change_tiles',
        'change_tile_states'
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
                'enum': [
                    '1m|1m|1m',
                    '2m|2m|2m',
                    '3m|3m|3m',
                    '4m|4m|4m',
                    '0m|5m|5m',
                    '5m|5m|5m',
                    '6m|6m|6m',
                    '7m|7m|7m',
                    '8m|8m|8m',
                    '9m|9m|9m',
                    '1p|1p|1p',
                    '2p|2p|2p',
                    '3p|3p|3p',
                    '4p|4p|4p',
                    '0p|5p|5p',
                    '5p|5p|5p',
                    '6p|6p|6p',
                    '7p|7p|7p',
                    '8p|8p|8p',
                    '9p|9p|9p',
                    '1s|1s|1s',
                    '2s|2s|2s',
                    '3s|3s|3s',
                    '4s|4s|4s',
                    '0s|5s|5s',
                    '5s|5s|5s',
                    '6s|6s|6s',
                    '7s|7s|7s',
                    '8s|8s|8s',
                    '9s|9s|9s',
                    '1z|1z|1z',
                    '2z|2z|2z',
                    '3z|3z|3z',
                    '4z|4z|4z',
                    '5z|5z|5z',
                    '6z|6z|6z',
                    '7z|7z|7z'
                ]
            },
            'additionalItems': False
        },
        'change_tiles': {
            '$comment': 'TODO: 詳細不明．',
            'type': 'array',
            'maxItems': 0,
            'additionalItems': False
        },
        'change_tile_states': {
            '$comment': 'TODO: 詳細不明．',
            'type': 'array',
            'minItems': 0,
            'additionalItems': False
        }
    },
    'additionalProperties': False
}


_RONG_OPTION_SCHEMA = {
    'title': '栄和の選択肢',
    'type': 'object',
    'required': [
        'type',
        'combination',
        'change_tiles',
        'change_tile_states'
    ],
    'properties': {
        'type': {
            'const': 9
        },
        'combination': {
            'type': 'array',
            'maxItems': 0,
            'additionalItems': False
        },
        'change_tiles': {
            '$comment': 'TODO: 詳細不明．',
            'type': 'array',
            'maxItems': 0,
            'additionalItems': False
        },
        'change_tile_states': {
            '$comment': 'TODO: 詳細不明．',
            'type': 'array',
            'maxItems': 0,
            'additionalItems': False
        }
    },
    'additionalProperties': False
}


_DAPAI_OPTION_PRESENCE_SCHEMA = {
    'title': '打牌に対する選択肢提示',
    'type': 'object',
    'required': [
        'seat',
        'operation_list',
        'time_add',
        'time_fixed'
    ],
    'properties': {
        'seat': _SEAT_SCHEMA,
        'operation_list': {
            'type': 'array',
            'minItems': 1,
            'items': {
                'oneOf': [
                    _CHI_OPTION_SCHEMA,
                    _PENG_OPTION_SCHEMA,
                    _DAMINGGANG_OPTION_SCHEMA,
                    _RONG_OPTION_SCHEMA
                ]
            },
            'additionalItems': False
        },
        'time_add': {
            'title': '追加考慮時間（ミリ秒）',
            'type': 'integer',
            'minimum': 0
        },
        'time_fixed': {
            'title': '基本考慮時間（ミリ秒）',
            'type': 'integer',
            'minimum': 0
        }
    },
    'additionalProperties': False
}


_DISCARD_TILE_SCHEMA = {
    'title': '打牌',
    'type': 'object',
    'required': [
        'seat',
        'tile',
        'is_liqi',
        'moqie',
        'zhenting',
        'tingpais',
        'doras',
        'is_wliqi',
        'operations',
        'tile_state'
    ],
    'properties': {
        'seat': _SEAT_SCHEMA,
        'tile': _TILE_SCHEMA,
        'is_liqi': {
            'title': '立直フラグ',
            'description': 'false: 立直宣言ではない, true: 立直宣言である',
            'type': 'boolean'
        },
        'moqie': {
            'title': '自摸切りフラグ',
            'description': 'false: 手出し, true: 自摸切り',
            'type': 'boolean'
        },
        'zhenting': _ZHENTING_SCHEMA,
        'tingpais': {
            'title': '聴牌情報',
            'type': 'array',
            'items': _TINGPAI_SCHEMA,
            'additionalItems': False
        },
        'doras': {
            'title': 'ドラ',
            'description': '嶺上牌の自摸後の打牌時にのみ要素が存在する．新旧全てのドラを含む．',
            'type': 'array',
            'items': _TILE_SCHEMA,
            'additionalItems': False
        },
        'is_wliqi': {
            'title': 'ダブル立直フラグ',
            'description': 'false: ダブル立直宣言ではない, true: ダブル立直宣言である',
            'type': 'boolean'
        },
        'operations': {
            'title': '当該打牌に対する他家の選択肢',
            'type': 'array',
            'items': _DAPAI_OPTION_PRESENCE_SCHEMA,
            'additionalItems': False
        },
        'tile_state': {
            '$comment': 'TODO: 詳細不明．',
            'const': 0
        }
    },
    'additionalProperties': False
}


_CHI_SCHEMA = {
    'title': 'チー',
    'type': 'object',
    'required': [
        'seat',
        'type',
        'tiles',
        'froms',
        'zhenting',
        'operation',
        'tile_states'
    ],
    'properties': {
        'seat': _SEAT_SCHEMA,
        'type': {
            'const': 0
        },
        'tiles': {
            'title': 'チーの対象牌',
            'description': '0番目と1番目の要素が手牌にあった牌．2番目の要素が鳴いた牌．',
            'enum': [
                ['2m', '3m', '1m'],
                ['1m', '3m', '2m'],
                ['3m', '4m', '2m'],
                ['1m', '2m', '3m'],
                ['2m', '4m', '3m'],
                ['4m', '0m', '3m'],
                ['4m', '5m', '3m'],
                ['2m', '3m', '4m'],
                ['3m', '0m', '4m'],
                ['3m', '5m', '4m'],
                ['0m', '6m', '4m'],
                ['5m', '6m', '4m'],
                ['3m', '4m', '0m'],
                ['4m', '6m', '0m'],
                ['6m', '7m', '0m'],
                ['3m', '4m', '5m'],
                ['4m', '6m', '5m'],
                ['6m', '7m', '5m'],
                ['4m', '0m', '6m'],
                ['4m', '5m', '6m'],
                ['0m', '7m', '6m'],
                ['5m', '7m', '6m'],
                ['7m', '8m', '6m'],
                ['0m', '6m', '7m'],
                ['5m', '6m', '7m'],
                ['6m', '8m', '7m'],
                ['8m', '9m', '7m'],
                ['6m', '7m', '8m'],
                ['7m', '9m', '8m'],
                ['7m', '8m', '9m'],
                ['2p', '3p', '1p'],
                ['1p', '3p', '2p'],
                ['3p', '4p', '2p'],
                ['1p', '2p', '3p'],
                ['2p', '4p', '3p'],
                ['4p', '0p', '3p'],
                ['4p', '5p', '3p'],
                ['2p', '3p', '4p'],
                ['3p', '0p', '4p'],
                ['3p', '5p', '4p'],
                ['0p', '6p', '4p'],
                ['5p', '6p', '4p'],
                ['3p', '4p', '0p'],
                ['4p', '6p', '0p'],
                ['6p', '7p', '0p'],
                ['3p', '4p', '5p'],
                ['4p', '6p', '5p'],
                ['6p', '7p', '5p'],
                ['4p', '0p', '6p'],
                ['4p', '5p', '6p'],
                ['0p', '7p', '6p'],
                ['5p', '7p', '6p'],
                ['7p', '8p', '6p'],
                ['0p', '6p', '7p'],
                ['5p', '6p', '7p'],
                ['6p', '8p', '7p'],
                ['8p', '9p', '7p'],
                ['6p', '7p', '8p'],
                ['7p', '9p', '8p'],
                ['7p', '8p', '9p'],
                ['2s', '3s', '1s'],
                ['1s', '3s', '2s'],
                ['3s', '4s', '2s'],
                ['1s', '2s', '3s'],
                ['2s', '4s', '3s'],
                ['4s', '0s', '3s'],
                ['4s', '5s', '3s'],
                ['2s', '3s', '4s'],
                ['3s', '0s', '4s'],
                ['3s', '5s', '4s'],
                ['0s', '6s', '4s'],
                ['5s', '6s', '4s'],
                ['3s', '4s', '0s'],
                ['4s', '6s', '0s'],
                ['6s', '7s', '0s'],
                ['3s', '4s', '5s'],
                ['4s', '6s', '5s'],
                ['6s', '7s', '5s'],
                ['4s', '0s', '6s'],
                ['4s', '5s', '6s'],
                ['0s', '7s', '6s'],
                ['5s', '7s', '6s'],
                ['7s', '8s', '6s'],
                ['0s', '6s', '7s'],
                ['5s', '6s', '7s'],
                ['6s', '8s', '7s'],
                ['8s', '9s', '7s'],
                ['6s', '7s', '8s'],
                ['7s', '9s', '8s'],
                ['7s', '8s', '9s']
            ]
        },
        'froms': {
            'title': 'チーの対象となった牌がどの席から出たか',
            'description': '0番目と1番目の要素は自席番号，2番目の要素が上家の席番号になる．',
            'enum': [
                [0, 0, 3],
                [1, 1, 0],
                [2, 2, 1],
                [3, 3, 2]
            ]
        },
        'liqi': _PREV_LIZHI_SCHEMA,
        'zhenting': _ZHENTING_SCHEMA,
        'operation': _ZIMO_OPTION_PRESENCE_SCHEMA,
        'tile_states': {
            '$comment': 'TODO: 詳細を調査すること．',
            'type': 'array',
            'minItems': 2,
            'maxItems': 2,
            'items': {
                'const': 0
            },
            'additionalItems': False
        }
    },
    'additionalProperties': False
}


_PENG_SCHEMA = {
    'title': 'ポン',
    'type': 'object',
    'required': [
        'seat',
        'type',
        'tiles',
        'froms',
        'zhenting',
        'operation',
        'tile_states'
    ],
    'properties': {
        'seat': _SEAT_SCHEMA,
        'type': {
            'const': 1
        },
        'tiles': {
            'title': 'ポンの対象牌',
            'description': '0番目と1番目の要素が手牌にあった牌．2番目の要素が鳴いた牌．',
            'enum': [
                ['1m', '1m', '1m'],
                ['2m', '2m', '2m'],
                ['3m', '3m', '3m'],
                ['4m', '4m', '4m'],
                ['5m', '5m', '0m'],
                ['0m', '5m', '5m'],
                ['5m', '5m', '5m'],
                ['6m', '6m', '6m'],
                ['7m', '7m', '7m'],
                ['8m', '8m', '8m'],
                ['9m', '9m', '9m'],
                ['1p', '1p', '1p'],
                ['2p', '2p', '2p'],
                ['3p', '3p', '3p'],
                ['4p', '4p', '4p'],
                ['5p', '5p', '0p'],
                ['0p', '5p', '5p'],
                ['5p', '5p', '5p'],
                ['6p', '6p', '6p'],
                ['7p', '7p', '7p'],
                ['8p', '8p', '8p'],
                ['9p', '9p', '9p'],
                ['1s', '1s', '1s'],
                ['2s', '2s', '2s'],
                ['3s', '3s', '3s'],
                ['4s', '4s', '4s'],
                ['5s', '5s', '0s'],
                ['0s', '5s', '5s'],
                ['5s', '5s', '5s'],
                ['6s', '6s', '6s'],
                ['7s', '7s', '7s'],
                ['8s', '8s', '8s'],
                ['9s', '9s', '9s'],
                ['1z', '1z', '1z'],
                ['2z', '2z', '2z'],
                ['3z', '3z', '3z'],
                ['4z', '4z', '4z'],
                ['5z', '5z', '5z'],
                ['6z', '6z', '6z'],
                ['7z', '7z', '7z']
            ]
        },
        'froms': {
            'title': 'ポンの対象となった牌がどの席から出たか',
            'description': '0番目と1番目の要素は自席番号，2番目の要素が対象の牌を打牌した席番号になる．',
            'enum': [
                [0, 0, 1],
                [0, 0, 2],
                [0, 0, 3],
                [1, 1, 0],
                [1, 1, 2],
                [1, 1, 3],
                [2, 2, 0],
                [2, 2, 1],
                [2, 2, 3],
                [3, 3, 0],
                [3, 3, 1],
                [3, 3, 2]
            ]
        },
        'liqi': _PREV_LIZHI_SCHEMA,
        'zhenting': _ZHENTING_SCHEMA,
        'operation': _ZIMO_OPTION_PRESENCE_SCHEMA,
        'tile_states': {
            '$comment': 'TODO: 詳細を調査すること．',
            'type': 'array',
            'minItems': 2,
            'maxItems': 2,
            'items': {
                'const': 0
            },
            'additionalItems': False
        }
    },
    'additionalProperties': False
}


_GANG_SCHEMA = {
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
        'seat': _SEAT_SCHEMA,
        'type': {
            'const': 2
        },
        'tiles': {
            'title': '大明槓の対象牌',
            'description': '0番目から2番目の要素が手牌にあった牌．3番目の要素が鳴いた牌．',
            'enum': [
                ['1m', '1m', '1m', '1m'],
                ['2m', '2m', '2m', '2m'],
                ['3m', '3m', '3m', '3m'],
                ['4m', '4m', '4m', '4m'],
                ['5m', '5m', '5m', '0m'],
                ['0m', '5m', '5m', '5m'],
                ['6m', '6m', '6m', '6m'],
                ['7m', '7m', '7m', '7m'],
                ['8m', '8m', '8m', '8m'],
                ['9m', '9m', '9m', '9m'],
                ['1p', '1p', '1p', '1p'],
                ['2p', '2p', '2p', '2p'],
                ['3p', '3p', '3p', '3p'],
                ['4p', '4p', '4p', '4p'],
                ['5p', '5p', '5p', '0p'],
                ['0p', '5p', '5p', '5p'],
                ['6p', '6p', '6p', '6p'],
                ['7p', '7p', '7p', '7p'],
                ['8p', '8p', '8p', '8p'],
                ['9p', '9p', '9p', '9p'],
                ['1s', '1s', '1s', '1s'],
                ['2s', '2s', '2s', '2s'],
                ['3s', '3s', '3s', '3s'],
                ['4s', '4s', '4s', '4s'],
                ['5s', '5s', '5s', '0s'],
                ['0s', '5s', '5s', '5s'],
                ['6s', '6s', '6s', '6s'],
                ['7s', '7s', '7s', '7s'],
                ['8s', '8s', '8s', '8s'],
                ['9s', '9s', '9s', '9s'],
                ['1z', '1z', '1z', '1z'],
                ['2z', '2z', '2z', '2z'],
                ['3z', '3z', '3z', '3z'],
                ['4z', '4z', '4z', '4z'],
                ['5z', '5z', '5z', '5z'],
                ['6z', '6z', '6z', '6z'],
                ['7z', '7z', '7z', '7z'],
                ['8z', '8z', '8z', '8z'],
                ['9z', '9z', '9z', '9z']
            ]
        },
        'froms': {
            'title': '大明槓の対象となった牌がどの席から出たか',
            'description': '0番目から2番目の要素は自席番号，3番目の要素が対象の牌を打牌した席番号になる．',
            'enum': [
                [0, 0, 0, 1],
                [0, 0, 0, 2],
                [0, 0, 0, 3],
                [1, 1, 1, 0],
                [1, 1, 1, 2],
                [1, 1, 1, 3],
                [2, 2, 2, 0],
                [2, 2, 2, 1],
                [2, 2, 2, 3],
                [3, 3, 3, 0],
                [3, 3, 3, 1],
                [3, 3, 3, 2]
            ]
        },
        'liqi': _PREV_LIZHI_SCHEMA,
        'zhenting': _ZHENTING_SCHEMA,
        'tile_states': {
            '$comment': 'TODO: 詳細を調査すること．',
            'type': 'array',
            'minItems': 3,
            'maxItems': 3,
            'items': {
                'const': 0
            },
            'additionalItems': False
        }
    },
    'additionalProperties': False
}


_CHI_PENG_GANG_SCHEMA = {
    'title': 'チー・ポン・カン',
    'oneOf': [
        _CHI_SCHEMA,
        _PENG_SCHEMA,
        _GANG_SCHEMA
    ]
}


_AN_GANG_SCHEMA = {
    'title': '暗槓',
    'type': 'object',
    'required': [
        'seat',
        'type',
        'tiles',
        'doras',
        'operations'
    ],
    'properties': {
        'seat': _SEAT_SCHEMA,
        'type': {
            'const': 3
        },
        'tiles': _TILE_SCHEMA,
        'doras': {
            'title': '表ドラ表示牌',
            '$comment': 'TODO: 暗槓時の表ドラ表示牌．新ドラは含まない．空配列の時もあって詳細不明．',
            'type': 'array',
            'items': _TILE_SCHEMA,
            'additionalItems': False
        },
        'operations': {
            'title': '槍槓の選択肢',
            'description': '暗槓に対する他家の槍槓の選択肢．国士無双和了に限る．',
            '$comment': '`_DAPAI_OPTION_PRESENCE_SCHEMA` を許しているが実際にはロンのみ．',
            'type': 'array',
            'maxItems': 3,
            'items': _DAPAI_OPTION_PRESENCE_SCHEMA,
            'additionalItems': False
        }
    },
    'additionalProperties': False
}


_ADD_GANG_SCHEMA = {
    'title': '加槓',
    'type': 'object',
    'required': [
        'seat',
        'type',
        'tiles',
        'doras',
        'operations'
    ],
    'properties': {
        'seat': _SEAT_SCHEMA,
        'type': {
            'const': 2
        },
        'tiles': _TILE_SCHEMA,
        'doras': {
            'title': '表ドラ表示牌',
            '$comment': 'TODO: 加槓時の表ドラ表示牌．新ドラは含まない．空配列の時もあって詳細不明．',
            'type': 'array',
            'items': _TILE_SCHEMA,
            'additionalItems': False
        },
        'operations': {
            'title': '槍槓の選択肢',
            'description': '加槓に対する他家の槍槓の選択肢．',
            '$comment': '`_DAPAI_OPTION_PRESENCE_SCHEMA` を許しているが実際にはロンのみ．',
            'type': 'array',
            'maxItems': 3,
            'items': _DAPAI_OPTION_PRESENCE_SCHEMA,
            'additionalItems': False
        }
    },
    'additionalProperties': False
}


_AN_GANG_ADD_GANG_SCHEMA = {
    'title': '暗槓・加槓',
    'oneOf': [
        _AN_GANG_SCHEMA,
        _ADD_GANG_SCHEMA
    ]
}


_HULE_SCHEMA = {
    'title': '和了',
    'type': 'object',
    'required': [
        'hules',
        'old_scores',
        'delta_scores',
        'wait_timeout',
        'scores',
        'gameend',
        'doras'
    ],
    'properties': {
        'hules': {
            'type': 'array',
            'minItems': 1,
            'maxItems': 3,
            'items': {
                'type': 'object',
                'required': [
                    'hand',
                    'ming',
                    'hu_tile',
                    'seat',
                    'zimo',
                    'qinjia',
                    'liqi',
                    'doras',
                    'li_doras',
                    'yiman',
                    'count',
                    'fans',
                    'fu',
                    'title',
                    'point_rong',
                    'point_zimo_qin',
                    'point_zimo_xian',
                    'title_id',
                    'point_sum',
                    'dadian'
                ],
                'properties': {
                    'hand': {
                        'title': '和了時の手牌',
                        'type': 'array',
                        'minItems': 1,
                        'maxItems': 13,
                        'items': _TILE_SCHEMA,
                        'additionalItems': False
                    },
                    'ming': {
                        'title': '和了時の副露牌',
                        'description': '"shunzi(X,Y,Z)": チー, "kezi(X,Y,Z)": ポン, "minggang(X,Y,Z,W)": 明槓, "angang(X,Y,Z,W)": 暗槓',
                        'type': 'array',
                        'maxItems': 4,
                        'items': {
                            'type': 'string'
                        },
                        'additionalItems': False
                    },
                    'hu_tile': _TILE_SCHEMA,
                    'seat': _SEAT_SCHEMA,
                    'zimo': {
                        'title': '自模和フラグ',
                        'type': 'boolean'
                    },
                    'qinjia': {
                        'title': '庄家（親）フラグ',
                        'type': 'boolean'
                    },
                    'liqi': {
                        'title': '立直フラグ',
                        'type': 'boolean'
                    },
                    'doras': {
                        'title': '表ドラ表示牌',
                        'type': 'array',
                        'minItems': 1,
                        'maxItems': 5,
                        'items': _TILE_SCHEMA,
                        'additionalItems': False
                    },
                    'li_doras': {
                        'title': '裏ドラ表示牌',
                        'type': 'array',
                        'maxItems': 5,
                        'items': _TILE_SCHEMA,
                        'additionalItems': False
                    },
                    'yiman': {
                        'title': '役満フラグ',
                        'description': 'false: 三倍満以下, true: 役満以上',
                        'type': 'boolean'
                    },
                    'count': {
                        'title': '翻数',
                        'description': '役満以上の場合，役満ならば1，二倍役満ならば2，三倍役満ならば3，以下同様．',
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
                                    'description': '裏ドラの場合に0がありうる．また役満以上の場合，役満ならば1，二倍役満ならば2．',
                                    'type': 'integer',
                                    'minimum': 0
                                },
                                'id': {
                                    'title': '役 ID',
                                    'description': '1: 門前清自摸和, '
                                                   '2: 立直, '
                                                   '3: 槍槓, '
                                                   '4: 嶺上開花, '
                                                   '5: 海底摸月, '
                                                   '6: 河底撈魚, '
                                                   '7: 役牌白, '
                                                   '8: 役牌發, '
                                                   '9: 役牌中, '
                                                   '10: 役牌:自風牌, '
                                                   '11: 役牌:場風牌, '
                                                   '12: 断幺九, '
                                                   '13: 一盃口, '
                                                   '14: 平和, '
                                                   '15: 混全帯幺九, '
                                                   '16: 一気通貫, '
                                                   '17: 三色同順, '
                                                   '18: ダブル立直, '
                                                   '19: 三色同刻, '
                                                   '20: 三槓子, '
                                                   '21: 対々和, '
                                                   '22: 三暗刻, '
                                                   '23: 小三元, '
                                                   '24: 混老頭, '
                                                   '25: 七対子, '
                                                   '26: 純全帯幺九, '
                                                   '27: 混一色, '
                                                   '28: 二盃口, '
                                                   '29: 清一色, '
                                                   '30: 一発, '
                                                   '31: ドラ, '
                                                   '32: 赤ドラ, '
                                                   '33: 裏ドラ, '
                                                   '35: 天和, '
                                                   '36: 地和, '
                                                   '37: 大三元, '
                                                   '38: 四暗刻, '
                                                   '39: 字一色, '
                                                   '40: 緑一色, '
                                                   '41: 清老頭, '
                                                   '42: 国士無双, '
                                                   '43: 小四喜, '
                                                   '44: 四槓子, '
                                                   '45: 九蓮宝燈, '
                                                   '47: 純正九蓮宝燈, '
                                                   '48: 四暗刻単騎, '
                                                   '49: 国士無双十三面待ち, '
                                                   '50: 大四喜',
                                    'type': 'integer',
                                    'enum': [
                                        1,
                                        2,
                                        3,
                                        4,
                                        5,
                                        6,
                                        7,
                                        8,
                                        9,
                                        10,
                                        11,
                                        12,
                                        13,
                                        14,
                                        15,
                                        16,
                                        17,
                                        18,
                                        19,
                                        20,
                                        21,
                                        22,
                                        23,
                                        24,
                                        25,
                                        26,
                                        27,
                                        28,
                                        29,
                                        30,
                                        31,
                                        32,
                                        33,
                                        35,
                                        36,
                                        37,
                                        38,
                                        39,
                                        40,
                                        41,
                                        42,
                                        43,
                                        44,
                                        45,
                                        47,
                                        48,
                                        49,
                                        50
                                    ]
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
                    'point_zimo_qin': {
                        'title': '散家（子）の自摸和の場合の庄家（親）の支払い',
                        'type': 'integer',
                        'minimum': 0
                    },
                    'point_zimo_xian': {
                        'title': '自摸和の場合の散家（子）の支払い',
                        'type': 'integer',
                        'minimum': 0
                    },
                    'title_id': {
                        'description': '0: 満貫未満, '
                                       '1: 満貫, '
                                       '2: 跳満, '
                                       '3: 倍満, '
                                       '4: 三倍満, '
                                       '5: 役満, '
                                       '6: 二倍役満, '
                                       '7: 三倍役満, '
                                       '11: 数え役満',
                        'enum': [
                            0,
                            1,
                            2,
                            3,
                            4,
                            5,
                            6,
                            7,
                            11
                        ]
                    },
                    'point_sum': {
                        'title': '得点',
                        'description': '和了の演出で右下に表示される数字．',
                        '$comment': 'TODO: 状況により詳細不明な値になることがある．',
                        'type': 'integer',
                        'minimum': 1000
                    },
                    'dadian': {
                        '$coment': 'TODO: 詳細不明．',
                        'const': 0
                    }
                },
                'additionalProperties': False
            },
            'additionalItems': False
        },
        'old_scores': {
            'title': '清算前点数',
            'type': 'array',
            'minItems': 3,
            'maxItems': 4,
            'items': {
                'type': 'integer'
            },
            'additionalItems': False
        },
        'delta_scores': {
            'title': '点数収支',
            'type': 'array',
            'minItems': 3,
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
        'scores': {
            'title': '清算後点数',
            'type': 'array',
            'minItems': 3,
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
                    'maxItems': 0,
                    'additionalItems': False
                }
            },
            'additionalProperties': False
        },
        'doras': {
            '$comment': 'TODO: 詳細不明．',
            'type': 'array',
            'maxItems': 0,
            'additionalItems': False
        }
    },
    'additionalProperties': False
}


_NO_TILE_SCHEMA = {
    'title': '荒牌平局',
    'type': 'object',
    'required': [
        'liujumanguan',
        'players',
        'scores',
        'gameend',
        'hules_history'
    ],
    'properties': {
        'liujumanguan': {
            'title': '流し満貫フラグ',
            'description': 'false: 流し満貫ではない, true: 流し満貫である',
            'type': 'boolean'
        },
        'players': {
            'type': 'array',
            'minItems': 3,
            'maxItems': 4,
            'items': {
                'type': 'object',
                'required': [
                    'tingpai',
                    'hand',
                    'tings',
                    'already_hule'
                ],
                'properties': {
                    'tingpai': {
                        'title': '聴牌フラグ',
                        'description': 'false: 不聴, true: 聴牌',
                        'type': 'boolean'
                    },
                    'hand': {
                        'title': '聴牌時の手牌',
                        'description': '不聴の場合は空配列',
                        'type': 'array',
                        'maxItems': 13,
                        'items': _TILE_SCHEMA,
                        'additionalItems': False
                    },
                    'tings': {
                        'type': 'array',
                        'items': _TINGPAI_SCHEMA,
                        'additionalItems': False
                    },
                    'already_hule': {
                        '$comment': 'TODO: 詳細不明．',
                        'const': False
                    }
                },
                'additionalProperties': False
            },
            'additionalItems': False
        },
        'scores': {
            'type': 'array',
            'minItems': 1,
            'maxItems': 2,
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
                    'seat': _SEAT_SCHEMA, # 流し満貫達成者．通常の荒牌平局では0．
                    'old_scores': {
                        'title': '開局時の点数',
                        'type': 'array',
                        'minItems': 3,
                        'maxItems': 4,
                        'items': {
                            'type': 'integer'
                        },
                        'additionalItems': False
                    },
                    'delta_scores': {
                        'title': '点数収支',
                        'description': '全員聴牌または全員不聴で点数収支が無い場合は空配列',
                        'type': 'array',
                        'maxItems': 4,
                        'items': {
                            'type': 'integer'
                        },
                        'additionalItems': False
                    },
                    'hand': {
                        'title': '流し満貫達成者の手牌',
                        'description': '通常の荒牌平局では空配列．',
                        '$comment': '流し満貫の達成に手牌は関係ないが，和了の演出を流用しているために便宜上必要と思われる．',
                        'type': 'array',
                        'maxItems': 13,
                        'items': _TILE_SCHEMA,
                        'additionalItems': False
                    },
                    'ming': {
                        'title': '流し満貫達成者の副露牌',
                        'description': '"shunzi(X,Y,Z)": チー, "kezi(X,Y,Z)": ポン, "minggang(X,Y,Z,W)": 明槓, "angang(X,Y,Z,W)": 暗槓',
                        '$comment': '雀魂の流し満貫は面前でなくても良い．',
                        'type': 'array',
                        'maxItems': 4,
                        'items': {
                            'type': 'string'
                        },
                        'additionalItems': False
                    },
                    'doras': {
                        'title': '流し満貫達成時の表ドラ表示牌',
                        'description': '通常の荒牌平局では空配列．',
                        '$comment': '流し満貫にドラは関係ないが，和了の演出を流用しているために便宜上必要と思われる．',
                        'type': 'array',
                        'maxItems': 5,
                        'items': _TILE_SCHEMA,
                        'additionalItems': False
                    },
                    'score': {
                        'title': '流し満貫達成時の得点',
                        'description': '通常の荒牌平局では0．',
                        '$comment': '流し満貫達成の演出（和了の演出を流用）で右下に表示される数字．',
                        'enum': [
                            0,
                            8000,
                            12000
                        ]
                    }
                },
                'additionalProperties': False
            },
            'additionalItems': False
        },
        'gameend': {
            '$comment': 'TODO: 詳細不明．',
            'const': False
        },
        'hules_history': {
            '$comment': 'TODO: 詳細不明．',
            'type': 'array',
            'maxItems': 0,
            'additionalItems': False
        }
    },
    'additionalProperties': False
}


_LIU_JU_SCHEMA = {
    'title': '途中流局',
    'oneOf': [
        {
            'title': '九種九牌',
            'type': 'object',
            'required': [
                'type',
                'seat',
                'tiles',
                'allplayertiles',
                'hules_history'
            ],
            'properties': {
                'type': {
                    'const': 1
                },
                'seat': _SEAT_SCHEMA,
                'tiles': {
                    'title': '九種九牌の場合の手牌',
                    'type': 'array',
                    'minItems': 14,
                    'maxItems': 14,
                    'items': _TILE_SCHEMA,
                    'additionalItems': False
                },
                'allplayertiles': {
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                },
                'hules_history': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
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
                'tiles',
                'allplayertiles',
                'hules_history'
            ],
            'properties': {
                'type': {
                    'const': 2
                },
                'seat': {
                    'const': 0
                },
                'tiles': {
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                },
                'allplayertiles': {
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                },
                'hules_history': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                }
            },
            'additionalProperties': False
        },
        {
            'title': '四槓散了',
            'type': 'object',
            'required': [
                'type',
                'seat',
                'tiles',
                'allplayertiles',
                'hules_history'
            ],
            'properties': {
                'type': {
                    'const': 3
                },
                'seat': {
                    'const': 0
                },
                'tiles': {
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                },
                'allplayertiles': {
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                },
                'hules_history': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                }
            },
            'additionalProperties': False
        },
        {
            'title': '四家立直',
            'type': 'object',
            'required': [
                'type',
                'seat',
                'tiles',
                'allplayertiles',
                'hules_history'
            ],
            'properties': {
                'type': {
                    'const': 4
                },
                'seat': {
                    'const': 0
                },
                'tiles': {
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                },
                'allplayertiles': {
                    'title': '四家立直成立時の全員の手牌',
                    'description': '手牌は牌を "|" で区切った文字列として表される．'
                                   '例えば "4m|5m|6m|1p|1p|0p|6p|7p|3s|4s|5s|5s|7s"．',
                    'type': 'array',
                    'minItems': 3,
                    'maxItems': 4,
                    'items': {
                        'type': 'string'
                    },
                    'additionalItems': False
                },
                'hules_history': {
                    '$comment': 'TODO: 詳細不明．',
                    'type': 'array',
                    'maxItems': 0,
                    'additionalItems': False
                }
            },
            'additionalProperties': False
        }
    ]
}


class ValidationError(RuntimeError):
    def __init__(
            self, uuid: str, chang: Optional[str], ju: Optional[int],
            ben: Optional[int], index: Optional[int],
            header: Optional[str], message: bytes, message_json: dict):
        if chang is None:
            assert(ju is None)
            assert(ben is None)
            assert(index is None)
            assert(header is None)
            super().__init__(
                f'''Failed to validate the detail of the game {uuid}:
message: {message}
json: {message_json}''')
            return

        assert(chang is not None)
        assert(ju is not None)
        assert(ben is not None)
        assert(index is not None)
        assert(header is not None)
        super().__init__(
            f'''Failed to validate the detail of the game {uuid},\
 {chang}{ju + 1}局{ben}本場, header = {header}, index = {index}:
message: {message}
json: {json.dumps(message_json)}''')


def validate(message: bytes) -> None:
    wrapper = Wrapper()
    wrapper.ParseFromString(message[3:])

    if wrapper.name != '':
        raise RuntimeError(f'''{wrapper.name}: An unexpected name.''')

    response = ResGameRecord()
    response.ParseFromString(wrapper.data)

    response_json = google.protobuf.json_format.MessageToDict(
        response, including_default_value_fields=True,
        preserving_proto_field_name=True)
    try:
        jsonschema.validate(
            instance=response_json, schema=_GAME_RECORD_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        logging.exception('Failed to validate the detail of a game.')
        uuid = response.head.uuid
        raise ValidationError(
            uuid, None, None, None, None, None, message, response_json)

    uuid = response.head.uuid

    wrapper = Wrapper()
    wrapper.ParseFromString(response.data)

    if wrapper.name != '.lq.GameDetailRecords':
        raise ValidationError(uuid, None, None, None, None, message,
                              response_json)

    records = GameDetailRecords()
    records.ParseFromString(wrapper.data)

    schema_list = [
        (b'^\n\x12\\.lq\\.RecordNewRound\x12', '.lq.RecordNewRound',
         RecordNewRound, _NEW_ROUND_SCHEMA),
        (b'^\n\x12\\.lq\\.RecordDealTile\x12', '.lq.RecordDealTile',
         RecordDealTile, _DEAL_TILE_SCHEMA),
        (b'^\n\x15\\.lq\\.RecordDiscardTile\x12',
         '.lq.RecordDiscardTile', RecordDiscardTile,
         _DISCARD_TILE_SCHEMA),
        (b'^\n\x15\\.lq\\.RecordChiPengGang\x12',
         '.lq.RecordChiPengGang', RecordChiPengGang,
         _CHI_PENG_GANG_SCHEMA),
        (b'^\n\x17\\.lq\\.RecordAnGangAddGang\x12',
         '.lq.RecordAnGangAddGang', RecordAnGangAddGang,
         _AN_GANG_ADD_GANG_SCHEMA),
        (b'^\n\x0e\\.lq\\.RecordHule\x12', '.lq.RecordHule', RecordHule,
         _HULE_SCHEMA),
        (b'^\n\x10\\.lq\\.RecordNoTile\x12', '.lq.RecordNoTile',
         RecordNoTile, _NO_TILE_SCHEMA),
        (b'^\n\x0f\\.lq\\.RecordLiuJu\x12', '.lq.RecordLiuJu',
         RecordLiuJu, _LIU_JU_SCHEMA)
    ]

    index = 0

    for record in records.records:
        name = None
        message_type = None
        schema = None
        for pattern, n, t, s in schema_list:
            m = re.search(pattern, record, re.DOTALL)
            if m is not None:
                name = n
                message_type = t
                schema = s
                break
        if name is None:
            assert(message_type is None)
            assert(schema is None)
            raise RuntimeError(f'An unknown record: {record}')

        assert(name is not None)
        assert(message_type is not None)
        assert(schema is not None)

        wrapper = Wrapper()
        wrapper.ParseFromString(record)

        if wrapper.name != name:
            raise RuntimeError(f'''{wrapper.name}: An unexpected name.''')

        parse = message_type()
        parse.ParseFromString(wrapper.data)

        if name == '.lq.RecordNewRound':
            chang = parse.chang
            chang = ['東', '南', '西'][chang]
            ju = parse.ju
            ben = parse.ben

        parse_json = google.protobuf.json_format.MessageToDict(
            parse, including_default_value_fields=True,
            preserving_proto_field_name=True)
        try:
            jsonschema.validate(instance=parse_json, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            logging.exception(f'''Failed to validate the record\
 `{name}` of the game {uuid}:
record: {record}
json: {json.dumps(parse_json)}''')
            raise ValidationError(uuid, chang, ju, ben, index, name,
                                  message, response_json)

        index += 1


def get_game_abstract(message: bytes) -> dict:
    wrapper = Wrapper()
    wrapper.ParseFromString(message[3:])

    if wrapper.name != '':
        raise RuntimeError(f'''{wrapper.name}: An unexpected name.''')

    parse = ResGameRecord()
    parse.ParseFromString(wrapper.data)

    uuid = parse.head.uuid
    start_time = parse.head.start_time
    start_time = datetime.datetime.fromtimestamp(
        start_time, tz=datetime.timezone.utc)

    return {
        'uuid': uuid,
        'start_time': start_time
    }
