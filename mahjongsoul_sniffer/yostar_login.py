#!/usr/bin/env python3

import re
import datetime
import pathlib
import pickle
import time
import base64
from typing import Optional
import googleapiclient.discovery
import mahjongsoul_sniffer.config as config_


class YostarLogin:
    def __init__(self, *, module_name: str):
        config = config_.get(module_name)

        yostar_login_config = config['yostar_login']
        self.__email_address = yostar_login_config['email_address']

        google_api_config = config['google_api']
        self.__google_api_token_path = google_api_config['token_path']
        self.__google_api_token_path = pathlib.Path(
            self.__google_api_token_path)
        if not self.__google_api_token_path.exists():
            raise RuntimeError(
                f'{self.__google_api_token_path}: File does not exist.')
        if not self.__google_api_token_path.is_file():
            raise RuntimeError(
                f'{self.__google_api_token_path}: Not a file.')

    def get_email_address(self) -> str:
        return self.__email_address

    def __get_auth_code(
            self, *, start_time: datetime.datetime) -> Optional[str]:
        with open(self.__google_api_token_path,
                  'rb') as google_api_token:
            google_api_creds = pickle.load(google_api_token)

        # https://github.com/googleapis/google-api-python-client/issues/299
        gmail_api = googleapiclient.discovery.build(
            'gmail', 'v1', cache_discovery=False,
            credentials=google_api_creds)

        messages = []
        query = f'from:info@mail.yostar.co.jp \
subject:Eメールアドレスの確認 \
to:{self.__email_address}'
        result = gmail_api.users().messages().list(
            userId='me', q=query).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
        while 'nextPageToken' in result:
            next_page_token = result['nextPageToken']
            result = gmail_api.users().messages().list(
                userId='me', pageToken=next_page_token).execute()
            messages.extend(result['messages'])
        message_ids = [message['id'] for message in messages]

        target_date = None
        target_body = None
        for message_id in message_ids:
            result = gmail_api.users().messages().get(
                userId='me', id=message_id).execute()
            payload = result['payload']

            date = None
            for header in payload['headers']:
                name = header['name']
                value = header['value']
                if name == 'From' and value != '<info@mail.yostar.co.jp>':
                    date = None
                    continue
                if name == 'To' and value != f'<{self.__email_address}>' :
                    date = None
                    continue
                if name == 'Date':
                    fmt = '%a, %d %b %Y %H:%M:%S %z'
                    date = datetime.datetime.strptime(value, fmt)
                    continue

            if date is None or date < start_time:
                continue

            if target_date is not None and date < target_date:
                continue

            target_date = date
            target_body = payload['body']['data']
            target_body = base64.urlsafe_b64decode(target_body).decode('UTF-8')

        if target_body is None:
            return None

        m = re.search('>(\\d{6})<', target_body)
        if m is None:
            return None

        return m.group(1)

    def get_auth_code(self, *, start_time: datetime.datetime,
                      timeout: datetime.timedelta) -> str:
        while True:
            auth_code = self.__get_auth_code(start_time=start_time)
            if auth_code is not None:
                break

            now = datetime.datetime.now(tz=datetime.timezone.utc)
            if now > start_time + timeout:
                raise RuntimeError(
                    'Extraction of the authentication has timed out.')
            time.sleep(1)
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            if now > start_time + timeout:
                raise RuntimeError(
                    'Extraction of the authentication has timed out.')

        return auth_code
