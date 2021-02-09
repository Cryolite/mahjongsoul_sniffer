#!/usr/bin/env python3

import datetime
import collections
import pathlib
import stat
import time
import logging
import json
from typing import (Optional, List)
import mahjongsoul_sniffer.config as config_
import mahjongsoul_sniffer.logging as logging_
import mahjongsoul_sniffer.redis as redis_


_CONFIG = config_.get('crawler_batch')


def _get_credentials():
    from oauth2client.file import Storage
    from oauth2client.client import OAuth2WebServerFlow

    client_id = _CONFIG['googleapi']['client_id']
    client_secret = _CONFIG['googleapi']['client_secret']

    credentials_path = pathlib.Path.home()
    if not credentials_path.exists():
        raise RuntimeError(
            f'''{credentials_path}: Directory does not exist.''')
    if not credentials_path.is_dir():
        raise RuntimeError(f'''{credentials_path}: Not a directory.''')
    credentials_path = credentials_path / '.googleapi'
    if not credentials_path.exists():
        raise RuntimeError(
            f'''{credentials_path}: Directory does not exist.''')
    if not credentials_path.is_dir():
        raise RuntimeError(f'''{credentials_path}: Not a directory.''')
    mode = stat.S_IMODE(credentials_path.stat().st_mode)
    if mode != 0o700:
        raise RuntimeError(f'''{credentials_path}: Expect the mode 0700\
 but {oct(mode)}.''')

    for basename in ['credentials', 'mahjongsoul-sniffer', 'crawler-batch']:
        credentials_path = credentials_path / basename
        if not credentials_path.exists():
            credentials_path.mkdir(mode=0o700)
        if not credentials_path.is_dir():
            raise RuntimeError(
                f'''{credentials_path}: Not a directory.''')
        mode = stat.S_IMODE(credentials_path.stat().st_mode)
        if mode != 0o700:
            raise RuntimeError(f'''{credentials_path}: Expect the mode\
 0700 but {oct(mode)}.''')

    credentials_path = credentials_path / 'credentials.json'

    storage = Storage(credentials_path)
    # `credentials_path` にファイルが無い場合，
    # `oauth2client.file.Storage.get` は None を返す．
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        flow = OAuth2WebServerFlow(
            client_id=client_id, client_secret=client_secret,
            scope='https://www.googleapis.com/auth/spreadsheets',
            redirect_uri='urn:ietf:wg:oauth:2.0:oob')
        url = flow.step1_get_authorize_url('urn:ietf:wg:oauth:2.0:oob')

        print('')
        print('以下の URL から許可コードを取得して入力してください．')
        print(url)
        print('')
        auth_code = input('許可コード: ').strip()

        credentials = flow.step2_exchange(auth_code)
        storage.put(credentials)

        print('')
        print('認証情報が保存されました．')

    if not credentials_path.exists():
        raise RuntimeError(
            f'''{credentials_path}: File does not exist.''')
    if not credentials_path.is_file():
        raise RuntimeError(f'''{credentials_path}: Not a file.''')
    mode = stat.S_IMODE(credentials_path.stat().st_mode)
    if mode != 0o600:
        raise RuntimeError(f'''{credentials_path}: Expect the mode\
 `0600' but `{oct(mode)}'.''')

    return credentials


def _get_spreadsheet_service(credentials):
    import httplib2
    from apiclient import discovery

    http = credentials.authorize(httplib2.Http())
    discovery_url = (
        'https://sheets.googleapis.com/$discovery/rest?version=v4')
    return discovery.build('sheets', 'v4', http=http,
                           discoveryServiceUrl=discovery_url)


def _num2date(num: int) -> datetime.date:
    return datetime.date(1899, 12, 30) + datetime.timedelta(days=num)


def _date2num(date: datetime.date) -> int:
    return (date - datetime.date(1899, 12, 30)).days


def _today() -> datetime.date:
    now = datetime.datetime.now(datetime.timezone.utc)
    return datetime.date(now.year, now.month, now.day)


class Sheet(object):
    def __init__(self):
        credentials = _get_credentials()
        self.__service = _get_spreadsheet_service(credentials)

        self.__spreadsheet_id = _CONFIG['spreadsheet']['id']

        spreadsheet = self.__service.spreadsheets().get(
            spreadsheetId=self.__spreadsheet_id).execute()

        self.__sheet_title = _CONFIG['spreadsheet']['sheet_title']

        self.__sheet_id = None
        for sheet in spreadsheet['sheets']:
            props = sheet['properties']
            if props['title'] == self.__sheet_title:
                self.__sheet_id = props['sheetId']
                break
        if self.__sheet_id is None:
            raise RuntimeError(f'''{self.__sheet_title}: No sheet with\
 such a title.''')

        # 見出し行以外の全てのセルのフォーマットを設定する．
        self.__set_cell_format()

        requests = []

        # 見出し行を固定する．
        requests.append({
            'updateSheetProperties': {
                'properties': {
                    'sheetId': self.__sheet_id,
                    'gridProperties': {
                        'frozenRowCount': 1
                    }
                },
                'fields': 'gridProperties.frozenRowCount'
            }
        })

        # 見出し行を設定する．
        headers = [
            '日付', 'abstractに関するコード変更内容', 'abstract',
            'abstract-alcyone', 'abstract-electra',
            'detailに関するコード変更内容', 'detail', 'error',
            '金の間・四人東', '金の間・四人南', '玉の間・四人東',
            '玉の間・四人南', '王座の間・四人東', '王座の間・四人南'
        ]
        headers = map(lambda h: {
            'userEnteredValue': {
                'stringValue': h
            },
            'userEnteredFormat': {
                'numberFormat': {
                    'type': 'TEXT'
                }
            }
        }, headers)
        requests.append({
            'updateCells': {
                'rows': [
                    {
                        'values': [h for h in headers]
                    }
                ],
                'fields': 'userEnteredValue.stringValue,userEnteredFormat.numberFormat',
                'start': {
                    'sheetId': self.__sheet_id,
                    'rowIndex': 0,
                    'columnIndex': 0
                }
            }
        })

        self.__service.spreadsheets().batchUpdate(
            spreadsheetId=self.__spreadsheet_id,
            body={'requests': requests}).execute()

        # 日付の降順でソートする．
        self.__sort()

    def __set_cell_format(self) -> None:
        # 見出し行以外の全てのセルのフォーマットを設定する．
        requests = []
        column_formats = (
            (0, 'DATE', 'yyyy/mm/dd'),
            (1, 'TEXT', None),
            (2, 'NUMBER', '0'),
            (3, 'NUMBER', '0'),
            (4, 'NUMBER', '0'),
            (5, 'TEXT', None),
            (6, 'NUMBER', '0'),
            (7, 'NUMBER', '0'),
            (8, 'NUMBER', '0'),
            (9, 'NUMBER', '0'),
            (10, 'NUMBER', '0'),
            (11, 'NUMBER', '0'),
            (12, 'NUMBER', '0'),
            (13, 'NUMBER', '0')
        )
        for column_index, column_type, column_pattern in column_formats:
            if column_pattern is not None:
                number_format = {
                    'type': column_type,
                    'pattern': column_pattern
                }
            else:
                number_format = {
                    'type': column_type
                }
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': self.__sheet_id,
                        'startRowIndex': 1,
                        'startColumnIndex': column_index,
                        'endColumnIndex': column_index + 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'numberFormat': number_format
                        }
                    },
                    'fields': 'userEnteredFormat.numberFormat'
                }
            })
        self.__service.spreadsheets().batchUpdate(
            spreadsheetId=self.__spreadsheet_id,
            body={'requests': requests}).execute()

    def __sort(self) -> None:
        # 日付の降順でソートする．
        requests = [{
            'sortRange': {
                'range': {
                    'sheetId': self.__sheet_id,
                    'startRowIndex': 1
                },
                'sortSpecs': [
                    {
                        'sortOrder': 'DESCENDING',
                        'dimensionIndex': 0
                    }
                ]
            }
        }]
        self.__service.spreadsheets().batchUpdate(
            spreadsheetId=self.__spreadsheet_id,
            body={'requests': requests}).execute()

    def __get_sheet(self, ranges: List[str]=[]) -> dict:
        spreadsheet = self.__service.spreadsheets().get(
            spreadsheetId=self.__spreadsheet_id, ranges=ranges,
            includeGridData=True).execute()

        sheet = None
        for s in spreadsheet['sheets']:
            props = s['properties']
            if props['sheetId'] == self.__sheet_id:
                sheet = s
                break
        if sheet is None:
            raise RuntimeError('No such a sheet.')

        return sheet

    def get_rows_by_date(self) -> dict:
        sheet = self.__get_sheet()

        if len(sheet['data']) != 1:
            raise RuntimeError(
                f'''{len(sheet['data'])}: An unexpected length.''')
        data = sheet['data'][0]

        result = {}
        for i, row in enumerate(data['rowData'][1:]):
            i += 1
            row = row['values']

            if len(row) == 0:
                raise RuntimeError(f'''No date in the {i}-th row.''')
            if len(row) > 14:
                raise RuntimeError(f'''The {i}-th row is too long.''')

            if all(map(lambda c: 'userEnteredValue' not in c, row)):
                # 空行を飛ばす．
                continue

            if 'userEnteredValue' not in row[0]:
                raise RuntimeError(f'''No value in the 0-th cell of the\
 {i}-th row.''')
            if 'numberValue' not in row[0]['userEnteredValue']:
                raise RuntimeError(f'''No number value in the 0-th cell\
 of the {i}-th row.''')
            type_ = type(row[0]['userEnteredValue']['numberValue'])
            if type_ is not int:
                raise RuntimeError(f'''Expect an integer in the 0-th\
 cell of the {i}-th row, but found a value of the type {type_}.''')

            date = _num2date(row[0]['userEnteredValue']['numberValue'])

            row.extend([None] * (14 - len(row)))
            assert(len(row) == 14)

            result[date] = []
            for j, cell in enumerate(row):
                if j == 0:
                    result[date].append(date)
                    continue
                if cell is None:
                    result[date].append(None)
                    continue
                if 'userEnteredValue' not in cell:
                    result[date].append(None)
                    continue
                cell_value = cell['userEnteredValue']
                if 'numberValue' in cell_value:
                    result[date].append(cell_value['numberValue'])
                    continue
                if 'stringValue' in cell_value:
                    result[date].append(cell_value['stringValue'])
                    continue
                raise RuntimeError(f'''An invalid value in the {j}-the\
 cell of the {i}-th row.''')

        return result

    def append_row(self, date: datetime.date) -> None:
        sheet = self.__get_sheet()

        if len(sheet['data']) != 1:
            raise RuntimeError(
                f'''{len(sheet['data'])}: An unexpected length.''')
        data = sheet['data'][0]

        # 空行を探す．
        row_index = None
        for i, row in enumerate(data['rowData'][1:]):
            i += 1
            row = row['values']
            if all(map(lambda c: 'userEnteredValue' not in c, row)):
                # 空行が見つかった．
                row_index = i
                break
            if 'userEnteredValue' not in row[0]:
                raise RuntimeError(f'''An invalid value of the 0-th\
 cell in the {i}-th row, which is not empty.''')
            if 'numberValue' not in row[0]['userEnteredValue']:
                raise RuntimeError(f'''An invalid value of the 0-th\
 cell in the {i}-th row, which is not empty.''')
            type_ = type(row[0]['userEnteredValue']['numberValue'])
            if type_ is not int:
                raise RuntimeError(f'''Expect an integer in the 0-th\
 cell of the {i}-th row, but found a value of the type {type_}.''')
            date_ = _num2date(row[0]['userEnteredValue']['numberValue'])
            if date_ == date:
                raise RuntimeError(f'''{date_.strftime('%Y/%m/%d')}: A\
 row already exists.''')

        if row_index is None:
            # 空行が無いのでシート全体の行数を増やす．
            row_index = sheet['properties']['gridProperties']['rowCount']
            assert(row_index > 0)
            requests = [{
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': self.__sheet_id,
                        'gridProperties': {
                            'rowCount': row_index * 2
                        }
                    },
                    'fields': 'gridProperties.rowCount'
                }
            }]
            self.__service.spreadsheets().batchUpdate(
                spreadsheetId=self.__spreadsheet_id,
                body={'requests': requests}).execute()

            # 見出し行以外の全てのセルのフォーマットを設定する．
            self.__set_cell_format()

        # 新しい行の0番目のセルに日付を入力する．
        requests = [{
            'updateCells': {
                'rows': [
                    {
                        'values': [
                            {
                                'userEnteredValue': {
                                    'numberValue': _date2num(date)
                                }
                            }
                        ]
                    }
                ],
                'fields': 'userEnteredValue.numberValue',
                'start': {
                    'sheetId': self.__sheet_id,
                    'rowIndex': row_index,
                    'columnIndex': 0
                }
            }
        }]
        self.__service.spreadsheets().batchUpdate(
            spreadsheetId=self.__spreadsheet_id,
            body={'requests': requests}).execute()

        # 日付の降順でソートする．
        self.__sort()

    def __get_row_index_by_date(
            self, date: datetime.date) -> Optional[int]:
        sheet = self.__get_sheet(ranges=[f'{self.__sheet_title}!A:A'])

        if len(sheet['data']) != 1:
            raise RuntimeError(
                f'''{len(sheet['data'])}: An unexpected length.''')
        data = sheet['data'][0]

        for i, row in enumerate(data['rowData'][1:]):
            i += 1
            row = row['values']
            if 'userEnteredValue' not in row[0]:
                continue
            if 'numberValue' not in row[0]['userEnteredValue']:
                raise RuntimeError(f'''An invalid value of the 0-th\
 cell in the {i}-th row.''')
            type_ = type(row[0]['userEnteredValue']['numberValue'])
            if type_ is not int:
                raise RuntimeError(f'''Expect an integer in the 0-th\
 cell of the {i}-th row, but found a value of the type {type_}.''')
            date_ = _num2date(row[0]['userEnteredValue']['numberValue'])
            if date_ == date:
                return i

        return None

    def update_cell(self, date: datetime.date, column_index: int,
                    value: int) -> None:
        if type(date) is not datetime.date:
            raise RuntimeError(
                f'''{type(date)}: An invalid type for `date'.''')
        if column_index not in [2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13]:
            raise ValueError(f'''{column_index}: An invalid value for\
 `column_index'.''')
        if type(value) is not int:
            raise RuntimeError(
                f'''{type(value)}: An invalid type for `value'.''')

        row_index = self.__get_row_index_by_date(date)
        if row_index is None:
            raise RuntimeError(f'{date}: No such a row.')

        requests = [{
            'updateCells': {
                'rows': [
                    {
                        'values': [
                            {
                                'userEnteredValue': {
                                    'numberValue': value
                                }
                            }
                        ]
                    }
                ],
                'fields': 'userEnteredValue.numberValue',
                'start': {
                    'sheetId': self.__sheet_id,
                    'rowIndex': row_index,
                    'columnIndex': column_index
                }
            }
        }]
        self.__service.spreadsheets().batchUpdate(
            spreadsheetId=self.__spreadsheet_id,
            body={'requests': requests}).execute()

    def finalize(self) -> None:
        # `abstract', `abstract-alcyone', `abstract-electra' の数値の
        # 一致を背景色で可視化する．
        sheet = self.__get_sheet(ranges=[f'{self.__sheet_title}!A:A',
                                         f'{self.__sheet_title}!C:E',
                                         f'{self.__sheet_title}!I:N'])
        if len(sheet['data']) != 3:
            raise RuntimeError(
                f'''{len(sheet['data'])}: An unexpected length.''')

        data = sheet['data'][0]['rowData']
        counts0 = sheet['data'][1]['rowData']
        counts1 = sheet['data'][2]['rowData']
        if len(data) != len(counts0):
            raise RuntimeError()
        if len(data) != len(counts1):
            raise RuntimeError()
        for i in range(len(data)):
            data[i]['values'].extend(counts0[i]['values'])
            data[i]['values'].extend(counts1[i]['values'])

        requests = []
        for i, row in enumerate(data[1:]):
            i += 1
            row = row['values']
            if len(row) != 10:
                raise RuntimeError(
                    f'''{len(row)}: An unexpected length.''')

            if all(map(lambda c: 'userEnteredValue' not in c, row)):
                # 空行をスキップする．
                continue

            if 'userEnteredValue' not in row[0]:
                raise RuntimeError(
                    f'''No value in the 0-th cell of the {i}-th row.''')
            if 'numberValue' not in row[0]['userEnteredValue']:
                raise RuntimeError(f'''An invalid value of the 0-th\
 cell in the {i}-th row.''')
            date = _num2date(row[0]['userEnteredValue']['numberValue'])
            if (_today() - date).days <= 1:
                # 直近2日は数値が変わりうるので処理をスキップする．
                continue

            values = []
            for j, cell in enumerate(row[1:4]):
                if 'userEnteredValue' not in cell:
                    value = 0
                elif 'numberValue' not in cell['userEnteredValue']:
                    raise RuntimeError(f'''An invalid value of the\
 {j + 2}-th cell in the {i}-th row.''')
                else:
                    value = cell['userEnteredValue']['numberValue']
                    type_ = type(value)
                    if type_ is not int:
                        raise RuntimeError(f'''Expect an integer in the\
 {j + 2}-th cell of the {i}-th row, but found a value of the type\
 {type_}.''')
                values.append(value)

            if values.count(0) >= 2:
                continue

            values.append(0)
            assert(len(values) == 4)
            for j, cell in enumerate(row[4:10]):
                if 'userEnteredValue' not in cell:
                    value = 0
                elif 'numberValue' not in cell['userEnteredValue']:
                    raise RuntimeError(f'''An invalid value of the\
 {j + 8}-th cell in the {i}-th row.''')
                else:
                    value = cell['userEnteredValue']['numberValue']
                    type_ = type(value)
                    if type_ is not int:
                        raise RuntimeError(f'''Expect an integer in the\
 {j + 8}-th cell of the {i}-th row, but found a value of the type\
 {type_}.''')
                values[3] += value

            max_value = max(values)
            count = 0
            for value in values:
                if value == max_value:
                    count += 1
            assert(count > 0)

            if count == 1:
                flags = [False, False, False, False]
            else:
                flags = list(map(lambda v: v == max_value, values))

            for j, flag in enumerate(flags[:3]):
                if flag:
                    requests.append({
                        'updateCells': {
                            'rows': [
                                {
                                    'values': [
                                        {
                                            'userEnteredFormat': {
                                                'backgroundColor': {
                                                    'red': 0.0,
                                                    'green': 1.0,
                                                    'blue': 1.0
                                                }
                                            }
                                        }
                                    ]
                                }
                            ],
                            'fields': 'userEnteredFormat.backgroundColor',
                            'start': {
                                'sheetId': self.__sheet_id,
                                'rowIndex': i,
                                'columnIndex': j + 2
                            }
                        }
                    })

            if flags[3]:
                requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': self.__sheet_id,
                            'startRowIndex': i,
                            'endRowIndex': i + 1,
                            'startColumnIndex': 8,
                            'endColumnIndex': 14
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {
                                    'red': 0.0,
                                    'green': 1.0,
                                    'blue': 1.0
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.backgroundColor'
                    }
                })

        self.__service.spreadsheets().batchUpdate(
            spreadsheetId=self.__spreadsheet_id,
            body={'requests': requests}).execute()


class S3Bucket(object):
    def __init__(self):
        import boto3
        bucket_name = _CONFIG['s3']['bucket_name']
        s3 = boto3.resource('s3')
        self.__bucket = s3.Bucket(bucket_name)

    def get_num_objects(self, prefix: str) -> int:
        prefix.rstrip('/')
        prefix += '/'
        num = 0
        for obj in self.__bucket.objects.filter(Prefix=prefix):
            num += 1
        return num

    def get_num_games_by_type(self, date: datetime.date) -> List[int]:
        uuid2mode = {}
        for prefix in _CONFIG['s3']['game_abstract_key_prefixes']:
            prefix = prefix.rstrip('/')
            prefix += '/' + date.strftime('%Y/%m/%d/')
            for obj in self.__bucket.objects.filter(Prefix=prefix):
                body = obj.get()['Body'].read().decode('UTF-8')
                abstract = json.loads(body)
                uuid = abstract['uuid']
                mode = abstract['mode']
                if uuid not in uuid2mode:
                    uuid2mode[uuid] = mode
                elif uuid2mode[uuid] != mode:
                    raise RuntimeError(f'''{uuid}: {uuid2mode[uuid]}\
 and {mode} differs.''')

        mode_count = collections.Counter(uuid2mode.values())
        return [
            mode_count['段位戦・金の間・四人東風戦'],
            mode_count['段位戦・金の間・四人半荘戦'],
            mode_count['段位戦・玉の間・四人東風戦'],
            mode_count['段位戦・玉の間・四人半荘戦'],
            mode_count['段位戦・王座の間・四人東風戦'],
            mode_count['段位戦・王座の間・四人半荘戦']
        ]


def main():
    sheet = Sheet()
    rows = sheet.get_rows_by_date()

    s3_bucket = S3Bucket()

    today = _today()
    yesterday = today - datetime.timedelta(days=1)

    game_abstract_key_prefixes \
        = _CONFIG['s3']['game_abstract_key_prefixes']

    for date in [yesterday, today]:
        for i in range(3):
            if date not in rows:
                sheet_value = None
            elif rows[date][i + 2] is None:
                sheet_value = None
            else:
                sheet_value = rows[date][i + 2]
                if type(sheet_value) is not int:
                    raise RuntimeError(f'''The {i + 2}-th cell of the\
 {date.strftime('%Y/%m/%d')}'s row is expected to be an integer but\
 {type(sheet_value)}.''')

            key_prefix = game_abstract_key_prefixes[i]
            key_prefix = key_prefix.rstrip('/')
            key_prefix += '/' + date.strftime('%Y/%m/%d')
            bucket_value = s3_bucket.get_num_objects(key_prefix)

            if sheet_value is None:
                new_value = bucket_value
            else:
                new_value = max(sheet_value, bucket_value)

            if date not in rows:
                rows[date] = [None] * 14
                rows[date][0] = date
                sheet.append_row(date)
            rows[date][i + 2] = new_value
            sheet.update_cell(date, i + 2, new_value)

    # detail の数値が sheet に記録されていない最古の日付を探す．通常，
    # この日付の1日前および2日前の detail をクローラが現在進行形で
    # 取得中と考えられる．ただし，3台ある Game Abstract Crawler の
    # 稼働状況によって abstract, abstract-alcyone, abstract-electra の
    # オブジェクトの数に違いが生じている場合があるため，3日前までの
    # detail の数を計算している．
    ongoing_date_for_detail = None
    for date in rows.keys():
        if rows[date][6] is not None:
            continue
        if ongoing_date_for_detail is None:
            ongoing_date_for_detail = date
            continue
        if date < ongoing_date_for_detail:
            ongoing_date_for_detail = date

    ongoing_dates_for_detail = [
        ongoing_date_for_detail - datetime.timedelta(days=3),
        ongoing_date_for_detail - datetime.timedelta(days=2),
        ongoing_date_for_detail - datetime.timedelta(days=1),
        ongoing_date_for_detail
    ]

    game_detail_key_prefix = _CONFIG['s3']['game_detail_key_prefix']

    for date in ongoing_dates_for_detail:
        if date not in rows:
            continue

        key_prefix = game_detail_key_prefix.rstrip('/')
        key_prefix += '/' + date.strftime('%Y/%m/%d')
        value = s3_bucket.get_num_objects(key_prefix)

        if value > 0:
            rows[date][6] = value
            sheet.update_cell(date, 6, value)

    for date in rows.keys():
        if (today - date).days <= 1:
            continue
        if rows[date][2] is None:
            continue
        if rows[date][3] is None:
            continue
        if rows[date][4] is None:
            continue
        if rows[date][6] is not None:
            continue
        if rows[date][8] is not None:
            continue
        if rows[date][9] is not None:
            continue
        if rows[date][10] is not None:
            continue
        if rows[date][11] is not None:
            continue
        if rows[date][12] is not None:
            continue
        if rows[date][13] is not None:
            continue

        num_games = s3_bucket.get_num_games_by_type(date)
        assert(len(num_games) == 6)
        for j in range(6):
            rows[date][j + 8] = num_games[j]
            sheet.update_cell(date, j + 8, num_games[j])

    sheet.finalize()


if __name__ == '__main__':
    logging_.initialize(module_name='crawler_batch',
                        service_name='main')
    redis = redis_.Redis(module_name='crawler_batch')
    while True:
        redis.set_timestamp('main.heartbeat')
        logging.info('Start a batch process.')
        main()
        logging.info('Finish the batch process.')

        redis.set_timestamp('main.heartbeat')
        logging.info(f'''Sleep for {_CONFIG['interval']} seconds.''')
        time.sleep(_CONFIG['interval'])
