#!/usr/bin/env python3

import datetime
import random
import pathlib
import time
import logging
import sys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy
from selenium.webdriver import Chrome
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions \
    import (TimeoutException, UnexpectedAlertPresentException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains
import mahjongsoul_sniffer.logging as logging_
from mahjongsoul_sniffer.yostar_login import YostarLogin
import mahjongsoul_sniffer.redis as redis_
import mahjongsoul_sniffer.s3 as s3_
from mahjongsoul_sniffer.mahjongsoul_pb2 import (ResGameRecord, Wrapper)


_BROWSER_RESTARTS = 1000
_BROWSER_RESTART_INTERVAL = 3600

_RETRY_COUNT = 3
_RETRY_INTERVAL = 0


class RetryRequest(Exception):
    pass


class RestartRequest(Exception):
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

    rect = canvas.rect
    x -= rect['width'] / 2
    y -= rect['height'] / 2

    ActionChains(driver).move_to_element_with_offset(canvas, x, y).click().perform()


_SCREENSHOT_PREFIX = pathlib.Path(
    '/var/log/mahjongsoul-sniffer/game-detail-crawler')


def _get_screenshot(driver: WebDriver, name: str) -> None:
    if not _SCREENSHOT_PREFIX.exists():
        _SCREENSHOT_PREFIX.mkdir(exist_ok=True)
    if not _SCREENSHOT_PREFIX.is_dir():
        raise RuntimeError(
            f'`{_SCREENSHOT_PREFIX}` is not a directory.')
    screenshot_path = _SCREENSHOT_PREFIX / name
    driver.get_screenshot_as_file(str(screenshot_path))


def _after_login(
        fetch_time: datetime.datetime, canvas: WebElement,
        redis: redis_.Redis) -> None:
    login = False
    for i in range(60):
        time.sleep(1)
        login_timestamp = redis.get_websocket_message('login-beat')
        if login_timestamp is None:
            continue
        login_timestamp = login_timestamp['timestamp']
        if login_timestamp >= fetch_time:
            login = True
            break
    if not login:
        logging.warning('Failed to login.')
        raise RestartRequest
    time.sleep(5)

    _get_screenshot(driver, '06-ロビー.png')

    game_abstracts = []

    s3_bucket = s3_.Bucket(module_name='game_detail_crawler')

    count = 0

    while True:
        if len(game_abstracts) <= 100:
            game_abstracts = s3_bucket.get_game_abstracts(max_keys=1000)
            if len(game_abstracts) == 0:
                logging.warning('No game abstract is available. Sleep\
 for 1 minute...')
                time.sleep(60)
                continue
            game_abstracts.sort(key=lambda x: x['start_time'])
            count = min(10, len(game_abstracts))

        assert(len(game_abstracts) > 0)
        if count > 0:
            idx = 0
            count -= 1
        else:
            idx = random.randint(0, len(game_abstracts) - 1)
        game_abstract = game_abstracts[idx]
        game_abstracts.pop(idx)

        key = game_abstract['key']
        uuid = game_abstract['uuid']
        mode = game_abstract['mode']
        start_time = game_abstract['start_time']

        if s3_bucket.has_game_detail(game_abstract):
            logging.info(f'Found the detail of the game {uuid}.')
            s3_bucket.delete_object(key)
            logging.info(f'Deleted the abstract of the game {uuid}.')
            continue

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        if now - start_time < datetime.timedelta(days=1):
            continue

        try:
            driver.get(f'https://game.mahjongsoul.com/?paipu={uuid}')
        except TimeoutException:
            logging.warning(f'Timeout occurred while loading the URL\
 `https://game.mahjongsoul.com/?paipu={uuid}`.')
            raise RetryRequest

        got = False

        for i in range(180):
            game_detail = redis.get_websocket_message('game-detail')

            if game_detail is not None:
                redis.delete('game-detail')
                got = True
                logging.info(f'Got the detail of the game {uuid}.')
                break

            time.sleep(1)

        if not got:
            logging.warning(
                f'Failed to get the detail of the game {uuid}.')
            _get_screenshot(driver, '98-ゲーム詳細取得タイムアウト.png')
            raise RetryRequest

        wrapper = Wrapper()
        wrapper.ParseFromString(game_detail['response'][3:])
        if wrapper.name != '':
            raise RuntimeError(
                f'''{wrapper.name}: An unexpected name.''')

        response = ResGameRecord()
        response.ParseFromString(wrapper.data)
        error_code = response.error.code

        if error_code == 1203:
            # 「対戦が存在しません」
            logging.warning(f'{uuid}: 対戦が存在しません (error_code = {error_code})')
            s3_bucket.delete_object(key)
            logging.warning(f'Deleted the abstract of the game {uuid}.')
            continue

        if error_code != 0:
            raise RuntimeError(f'uuid = {uuid}, error_code = {error_code}')

        redis.rpush_websocket_message('game-detail-list', game_detail)


def _wait_for_page_to_present(driver: WebDriver) -> WebElement:
    canvas = WebDriverWait(driver, 60).until(
        ec.visibility_of_element_located((By.ID, 'layaCanvas')))
    time.sleep(15)
    return canvas


def main(driver: WebDriver) -> None:
    fetch_time = datetime.datetime.now(tz=datetime.timezone.utc)
    driver.get('https://game.mahjongsoul.com/')
    canvas = _wait_for_page_to_present(driver)
    _get_screenshot(driver, '00-ページ読み込み.png')

    yostar_login = YostarLogin(module_name='game_detail_crawler')

    # 「ログイン」ボタンをクリック
    click_canvas_within(driver, canvas, 540, 177, 167, 38)
    time.sleep(1)
    _get_screenshot(driver, '01-ログインボタンクリック.png')

    # 「メールアドレス」フォームをクリックしてフォーカスを移動
    click_canvas_within(driver, canvas, 145, 154, 291, 30)
    time.sleep(1)

    email_address = yostar_login.get_email_address()

    # 「メールアドレス」フォームにメールアドレスを入力
    ActionChains(driver).send_keys(email_address).perform()
    time.sleep(1)
    _get_screenshot(driver, '02-メールアドレス入力.png')

    # 「コードを受け取る」ボタンをクリック
    start_time = datetime.datetime.now(tz=datetime.timezone.utc)
    click_canvas_within(driver, canvas, 351, 206, 86, 36)
    time.sleep(1)
    _get_screenshot(driver, '03-コードを受け取るボタンクリック.png')

    # 「確認」ボタンをクリック
    click_canvas_within(driver, canvas, 378, 273, 60, 23)
    time.sleep(1)
    _get_screenshot(driver, '04-確認ボタンクリック.png')

    # 「認証コード」フォームをクリックしてフォーカスを移動
    click_canvas_within(driver, canvas, 144, 211, 196, 30)
    time.sleep(1)

    auth_code = yostar_login.get_auth_code(
        start_time=start_time, timeout=datetime.timedelta(minutes=1))

    # 「認証コード」フォームに認証コードを入力
    ActionChains(driver).send_keys(auth_code).perform()
    time.sleep(1)
    _get_screenshot(driver, '05-認証コード入力.png')

    # 「ログイン」ボタンをクリック
    click_canvas_within(driver, canvas, 209, 293, 163, 37)

    redis = redis_.Redis(module_name='game_detail_crawler')

    retry_count = 0
    while True:
        try:
            _after_login(fetch_time, canvas, redis)
        except RetryRequest:
            retry_count += 1

            timestamp = redis.get_timestamp('archiver.heartbeat')
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            idle_threshold = datetime.timedelta(minutes=3)
            if now - timestamp > idle_threshold:
                if retry_count > _RETRY_COUNT:
                    # 観戦画面表示を `_RETRY_COUNT` 回試みても
                    # `archiver` サービスがまったく動かなかった．つまり
                    #
                    #   - `archiver` サービスが停止している，
                    #   - ログインできなかった，もしくは
                    #   - 観戦画面への画面遷移が不可能になっている
                    #
                    # などの場合．
                    raise RuntimeError(f'The allowed number of retries\
 ({_RETRY_COUNT}) has been exceeded.')
            else:
                # `idle_threshold` 以内に一度は観戦画面への画面遷移が
                # できていた場合．
                retry_count = 0

            logging.warning(
                f'Retrying after {_RETRY_INTERVAL}-seconds sleep...')
            time.sleep(_RETRY_INTERVAL)


if __name__ == '__main__':
    logging_.initialize(
        module_name='game_detail_crawler', service_name='crawler')

    for screenshot_path in _SCREENSHOT_PREFIX.glob('*.png'):
        screenshot_path.unlink()
        logging.info(f'Deleted an old screenshot `{screenshot_path}`.')

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=800,600')
    options.add_argument('--proxy-server=localhost:8080')

    # If the user agent contains the string `HeadlessChrome`,
    # the browser is rejected from the login process of Majsoul.
    # Therefore, it is necessary to spoof the user agent.
    with Chrome(options=options) as driver:
        driver.get('https://www.google.com/')
        user_agent = driver.execute_script('return navigator.userAgent')
        user_agent = user_agent.replace('HeadlessChrome', 'Chrome')
    options.add_argument(f'--user-agent={user_agent}')

    browser_restarts = 0
    while True:
        with Chrome(options=options) as driver:
            try:
                main(driver)
                sys.exit()
            except RestartRequest as e:
                logging.info(
                    'Restarting the crawler after 5-minutes sleep...')
                time.sleep(300)
                continue
            except UnexpectedAlertPresentException as e:
                if e.alert_text == 'Laya3D init error,must support webGL!':
                    logging.warning(f'`Laya3D init error` occurred.  So,\
 restarting the browser after {_BROWSER_RESTART_INTERVAL}-seconds sleep...')
                    time.sleep(_BROWSER_RESTART_INTERVAL)
                    continue
                if e.alert_text == 'open failed':
                    logging.warning(f'`open failed` occurred. So, restarting\
 the browser after {_BROWSER_RESTART_INTERVAL}-seconds sleep...')
                    time.sleep(_BROWSER_RESTART_INTERVAL)
                    continue
                _get_screenshot(driver, '99-エラー.png')
                logging.exception('Abort with an unhandled exception.')
                raise
            except Exception as e:
                _get_screenshot(driver, '99-エラー.png')
                logging.exception('Abort with an unhandled exception.')
                browser_restarts += 1
                if browser_restarts > _BROWSER_RESTARTS:
                    logging.error(f'The allowed number of browser\
 restarts ({_BROWSER_RESTARTS}) has been exceeded.')
                    raise
                logging.warning(f'Restarting the browser after\
 {_BROWSER_RESTART_INTERVAL}-seconds sleep...')
                time.sleep(_BROWSER_RESTART_INTERVAL)
                continue
