#!/usr/bin/env python3

import datetime
import random
import pathlib
import time
import getpass
import typing
import yaml
import jsonschema
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Chrome
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains
import redis


_config_schema = {
    'type': 'object',
    'required': [
        'logging',
        'redis'
    ],
    'properties': {
        'logging': {
            'type': 'object',
            'required': ['log_file'],
            'properties': {
                'level': {
                    'enum': [
                        'DEBUG',
                        'INFO',
                        'WARNING',
                        'ERROR',
                        'CRITICAL',
                        None
                    ]
                },
                'log_file': {
                    'type': 'object',
                    'required': ['path'],
                    'properties': {
                        'path': {
                            'type': 'string'
                        },
                        'max_bytes': {
                            'oneOf': [
                                {
                                    'type': 'integer',
                                    'minimum': 0
                                },
                                {
                                    'const': None
                                }
                            ]
                        },
                        'backup_count': {
                            'oneOf': [
                                {
                                    'type': 'integer',
                                    'minimum': 0
                                },
                                {
                                    'const': None
                                }
                            ]
                        }
                    },
                    'additionalProperties': False
                }
            },
            'additionalProperties': False
        },
        'redis': {
            'type': 'object',
            'required': [
                'host'
            ],
            'properties': {
                'host': {
                    'type': 'string'
                },
                'port': {
                    'oneOf': [
                        {
                            'type': 'integer',
                            'minimum': 1
                        },
                        {
                            'const': None
                        }
                    ]
                }
            },
            'additionalProperties': False
        }
    },
    'additionalProperties': False
}


class Config(object):
    def __init__(self):
        config_file_path = pathlib.Path('config/game_abstract_crawler.yaml')
        if not config_file_path.exists():
            raise RuntimeError(
                f'Config file `{config_file_path}` does not exist.')
        if not config_file_path.is_file():
            raise RuntimeError(f'`{config_file_path}` is expected to be a'
                               ' config file but not a file.')

        with open(config_file_path) as config_file:
            config = yaml.load(config_file, Loader=yaml.Loader)
        jsonschema.validate(instance=config, schema=_config_schema)

        self._config = config

    @property
    def logging_level(self) -> str:
        if 'level' in self._config['logging']:
            logging_level = self._config['logging']['level']
            if logging_level is None:
                logging_level = 'INFO'
        else:
            logging_level = 'INFO'
        return logging_level

    @property
    def log_file_path(self) -> pathlib.Path:
        return self._config['logging']['log_file']['path']

    @property
    def log_file_max_bytes(self) -> typing.Optional[int]:
        if 'max_bytes' in self._config['logging']['log_file']:
            log_file_max_bytes = \
                self._config['logging']['log_file']['max_bytes']
            if log_file_max_bytes == 0:
                log_file_max_bytes = None
        else:
            log_file_max_bytes = None
        return log_file_max_bytes

    @property
    def log_file_backup_count(self) -> typing.Optional[int]:
        if 'backup_count' in self._config['logging']['log_file']:
            log_file_backup_count = \
                self._config['logging']['log_file']['backup_count']
            if log_file_backup_count == 0:
                log_file_backup_count = None
        else:
            log_file_backup_count = None
        return log_file_backup_count

    @property
    def redis_host(self) -> str:
        return self._config['redis']['host']

    @property
    def redis_port(self) -> int:
        if 'port' not in self._config['redis']:
            return 6379
        if self._config['redis']['port'] is None:
            return 6379
        return self._config['redis']['port']


config = Config()


class RefreshRequest(Exception):
    pass


def click_canvas_within(
        driver: WebDriver, canvas: WebElement,
        left: int, top: int, width: int, height: int) -> None:
    center_x = left + width / 2.0
    center_y = top + height / 2.0

    x_sigma = width / 4.0
    while True:
        x = int(random.normalvariate(center_x, x_sigma))
        if left <= x and x < left + width:
            break

    y_sigma = height / 4.0
    while True:
        y = int(random.normalvariate(center_y, y_sigma))
        if top <= y and y < top + height:
            break

    #print((x, y))
    ActionChains(driver).move_to_element_with_offset(canvas, x, y).click().perform()


def _get_screenshot(driver: WebDriver, name: str) -> None:
    game_abstract_crawler_log_prefix = pathlib.Path(
        '/var/log/mahjongsoul-sniffer/game-abstract-crawler')
    if not game_abstract_crawler_log_prefix.exists():
        raise RuntimeError(
            f'`{game_abstract_crawler_log_prefix}` does not exist.')
    screenshot_path = game_abstract_crawler_log_prefix / name
    driver.get_screenshot_as_file(str(screenshot_path))


def _raise_if_gets_stuck(r: redis.Redis) -> None:
    api_timestamp = r.hget('api-timestamp', 'fetchGameLiveList')
    if api_timestamp is None:
        raise RefreshRequest()
    api_timestamp = int(api_timestamp.decode('utf-8'))

    now = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())

    if now - api_timestamp > 60:
        raise RefreshRequest()


def _after_login(fetch_time: datetime.datetime, canvas: WebElement) -> None:
    r = redis.Redis(host=config.redis_host, port=config.redis_port)

    login = False
    for i in range(60):
        time.sleep(1)
        login_timestamp = r.hget('api-timestamp', 'loginBeat')
        if login_timestamp is None:
            continue
        login_timestamp = int(login_timestamp.decode('utf-8'))
        if login_timestamp >= int(fetch_time.timestamp()):
            login = True
            break
    if not login:
        raise RuntimeError('Failed to login.')
    time.sleep(5)

    _get_screenshot(driver, '06-ロビー.png')

    # 「観戦」ボタンをクリック
    click_canvas_within(driver, canvas, 491, 398, 51, 42)
    time.sleep(10)

    _get_screenshot(driver, '07-観戦ボタンクリック.png')

    while True:
        # 部屋のプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 60, 88, 157, 30)
        time.sleep(1)

        # 部屋のプルダウンメニューから「金の間」を選択
        click_canvas_within(driver, canvas, 60, 119, 134, 30)
        time.sleep(10)

        # モードのプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 241, 88, 157, 30)
        time.sleep(1)

        # モードのプルダウンメニューから「4人東風戦」を選択
        click_canvas_within(driver, canvas, 241, 119, 134, 30)
        time.sleep(10)

        _raise_if_gets_stuck(r)

        _get_screenshot(driver, '08-00-金の間・4人東風戦.png')

        # モードのプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 241, 88, 157, 30)
        time.sleep(1)

        # モードのプルダウンメニューから「4人半荘戦」を選択
        click_canvas_within(driver, canvas, 241, 150, 134, 30)
        time.sleep(10)

        _raise_if_gets_stuck(r)

        _get_screenshot(driver, '08-01-金の間・4人半荘戦.png')

        # 部屋のプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 60, 88, 157, 30)
        time.sleep(1)

        # 部屋のプルダウンメニューから「玉の間」を選択
        click_canvas_within(driver, canvas, 60, 150, 134, 30)
        time.sleep(10)

        # モードのプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 241, 88, 157, 30)
        time.sleep(1)

        # モードのプルダウンメニューから「4人東風戦」を選択
        click_canvas_within(driver, canvas, 241, 119, 134, 30)
        time.sleep(10)

        _raise_if_gets_stuck(r)

        _get_screenshot(driver, '08-02-玉の間・4人東風戦.png')

        # モードのプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 241, 88, 157, 30)
        time.sleep(1)

        # モードのプルダウンメニューから「4人半荘戦」を選択
        click_canvas_within(driver, canvas, 241, 150, 134, 30)
        time.sleep(10)

        _raise_if_gets_stuck(r)

        _get_screenshot(driver, '08-03-玉の間・4人半荘戦.png')

        # 部屋のプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 60, 88, 157, 30)
        time.sleep(1)

        # 部屋のプルダウンメニューから「王座の間」を選択
        click_canvas_within(driver, canvas, 60, 182, 134, 30)
        time.sleep(10)

        # モードのプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 241, 88, 157, 30)
        time.sleep(1)

        # モードのプルダウンメニューから「4人東風戦」を選択
        click_canvas_within(driver, canvas, 241, 119, 134, 30)
        time.sleep(10)

        _raise_if_gets_stuck(r)

        _get_screenshot(driver, '08-04-王座の間・4人東風戦.png')

        # モードのプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 241, 88, 157, 30)
        time.sleep(1)

        # モードのプルダウンメニューから「4人半荘戦」を選択
        click_canvas_within(driver, canvas, 241, 150, 134, 30)
        time.sleep(10)

        _raise_if_gets_stuck(r)

        _get_screenshot(driver, '08-05-王座の間・4人半荘戦.png')


def _wait_for_page_to_present(driver: WebDriver) -> WebElement:
    canvas = WebDriverWait(driver, 60).until(
        ec.visibility_of_element_located((By.ID, 'layaCanvas'))
    )
    time.sleep(15)
    return canvas


def main(driver: WebDriver) -> None:
    fetch_time = datetime.datetime.now(tz=datetime.timezone.utc)
    driver.get('https://game.mahjongsoul.com/')
    canvas = _wait_for_page_to_present(driver)

    _get_screenshot(driver, '00-ページ読み込み.png')

    # 「ログイン」ボタンをクリック
    click_canvas_within(driver, canvas, 540, 177, 167, 38)
    time.sleep(1)

    _get_screenshot(driver, '01-ログインボタンクリック.png')

    mail_address = input('メールアドレス: ')

    # 「メールアドレス」フォームに入力
    click_canvas_within(driver, canvas, 145, 154, 291, 30)
    time.sleep(1)

    ActionChains(driver).send_keys(mail_address).perform()
    time.sleep(1)

    _get_screenshot(driver, '02-メールアドレス入力.png')

    # 「コードを受け取る」ボタンをクリック
    click_canvas_within(driver, canvas, 351, 206, 86, 36)
    time.sleep(1)

    _get_screenshot(driver, '03-コードを受け取るボタンクリック.png')

    # 「確認」ボタンをクリック
    click_canvas_within(driver, canvas, 378, 273, 60, 23)
    time.sleep(1)

    _get_screenshot(driver, '04-確認ボタンクリック.png')

    auth_code = getpass.getpass(prompt='認証コード: ',)

    # 「認証コード」フォームに入力
    click_canvas_within(driver, canvas, 144, 211, 196, 30)
    time.sleep(1)

    ActionChains(driver).send_keys(auth_code).perform()
    time.sleep(1)

    _get_screenshot(driver, '05-認証コード入力.png')

    # 「ログイン」ボタンをクリック
    click_canvas_within(driver, canvas, 209, 293, 163, 37)

    while True:
        try:
            _after_login(fetch_time, canvas)
        except RefreshRequest:
            print('Refresh was requested.')
            while True:
                fetch_time = datetime.datetime.now(tz=datetime.timezone.utc)
                try:
                    driver.refresh()
                    break
                except TimeoutException:
                    time.sleep(60)
            canvas = _wait_for_page_to_present(driver)
            continue


if __name__ == '__main__':
    log_prefix = pathlib.Path('/var/log/mahjongsoul-sniffer')
    if not log_prefix.exists():
        raise RuntimeError(f'`{log_prefix}` does not exist.')
    if not log_prefix.is_dir():
        raise RuntimeError(f'`{log_prefix}` is not a directory.')

    game_abstract_crawler_log_prefix = log_prefix / 'game-abstract-crawler'
    if not game_abstract_crawler_log_prefix.exists():
        game_abstract_crawler_log_prefix.mkdir()
    if not game_abstract_crawler_log_prefix.is_dir():
        raise RuntimeError(
            f'`{game_abstract_crawler_log_prefix}` is not a directory.')

    options = Options()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=800,600')
    with Chrome(options=options) as driver:
        try:
            main(driver)
        except Exception as e:
            _get_screenshot(driver, '99-エラー.png')
            raise
