#!/usr/bin/env python3

import datetime
import random
import pathlib
import time
import logging
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy
from selenium.webdriver.common.desired_capabilities \
    import DesiredCapabilities
from selenium.webdriver import Chrome
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains
import mahjongsoul_sniffer.config as config_
import mahjongsoul_sniffer.logging as logging_
import mahjongsoul_sniffer.redis as redis_
from mahjongsoul_sniffer.yostar_login import YostarLogin


_CONFIG = config_.get('game_abstract_crawler')['crawler']


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

    rect = canvas.rect
    x -= rect['width'] / 2
    y -= rect['height'] / 2

    ActionChains(driver).move_to_element_with_offset(canvas, x, y).click().perform()


_SCREENSHOT_PREFIX = pathlib.Path(
    '/var/log/mahjongsoul-sniffer/game-abstract-crawler')


def _get_screenshot(driver: WebDriver, name: str) -> None:
    if not _SCREENSHOT_PREFIX.exists():
        _SCREENSHOT_PREFIX.mkdir(exist_ok=True)
    if not _SCREENSHOT_PREFIX.is_dir():
        raise RuntimeError(
            f'`{_SCREENSHOT_PREFIX}` is not a directory.')
    screenshot_path = _SCREENSHOT_PREFIX / name
    driver.get_screenshot_as_file(str(screenshot_path))


def _raise_if_gets_stuck(
        redis: redis_.Redis, fetch_time: datetime.datetime) -> None:
    timestamp = redis.get_timestamp('archiver.heartbeat')
    if timestamp is None:
        raise RefreshRequest()
    if timestamp < fetch_time:
        raise RefreshRequest()


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
        fetch_time = datetime.datetime.now(tz=datetime.timezone.utc)
        click_canvas_within(driver, canvas, 241, 119, 134, 30)
        time.sleep(10)
        _raise_if_gets_stuck(redis, fetch_time)
        _get_screenshot(driver, '08-00-金の間・4人東風戦.png')

        # モードのプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 241, 88, 157, 30)
        time.sleep(1)

        # モードのプルダウンメニューから「4人半荘戦」を選択
        fetch_time = datetime.datetime.now(tz=datetime.timezone.utc)
        click_canvas_within(driver, canvas, 241, 150, 134, 30)
        time.sleep(10)
        _raise_if_gets_stuck(redis, fetch_time)
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
        fetch_time = datetime.datetime.now(tz=datetime.timezone.utc)
        click_canvas_within(driver, canvas, 241, 119, 134, 30)
        time.sleep(10)
        _raise_if_gets_stuck(redis, fetch_time)
        _get_screenshot(driver, '08-02-玉の間・4人東風戦.png')

        # モードのプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 241, 88, 157, 30)
        time.sleep(1)

        # モードのプルダウンメニューから「4人半荘戦」を選択
        fetch_time = datetime.datetime.now(tz=datetime.timezone.utc)
        click_canvas_within(driver, canvas, 241, 150, 134, 30)
        time.sleep(10)
        _raise_if_gets_stuck(redis, fetch_time)
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
        fetch_time = datetime.datetime.now(tz=datetime.timezone.utc)
        click_canvas_within(driver, canvas, 241, 119, 134, 30)
        time.sleep(10)
        _raise_if_gets_stuck(redis, fetch_time)
        _get_screenshot(driver, '08-04-王座の間・4人東風戦.png')

        # モードのプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 241, 88, 157, 30)
        time.sleep(1)

        # モードのプルダウンメニューから「4人半荘戦」を選択
        fetch_time = datetime.datetime.now(tz=datetime.timezone.utc)
        click_canvas_within(driver, canvas, 241, 150, 134, 30)
        time.sleep(10)
        _raise_if_gets_stuck(redis, fetch_time)
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

    yostar_login = YostarLogin(module_name='game_abstract_crawler')

    # 「ログイン」ボタンをクリック
    click_canvas_within(driver, canvas, 541, 178, 164, 35)
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

    redis = redis_.Redis(module_name='game_abstract_crawler')

    redis.delete('archiver.heartbeat')

    failure_count = 0

    while True:
        try:
            _after_login(fetch_time, canvas, redis)
        except RefreshRequest:
            failure_count += 1

            timestamp = redis.get_timestamp('archiver.heartbeat')

            if timestamp is None:
                if failure_count >= 3:
                    # ログイン～観戦画面表示を3回試みても
                    # `archiver` サービスがまったく動かなかった．つまり
                    #
                    #   - `archiver` サービスが停止している，
                    #   - ログインできなかった，もしくは
                    #   - 観戦画面への画面遷移が不可能になっている
                    #
                    # などの場合．
                    raise RuntimeError(
                        '`archiver` service does not seem to run.')
            else:
                # 一度は観戦画面への画面遷移ができていた場合．
                failure_count = 0

            # `archiver` サービスが5分以上動いていないならば
            # 例外を投げて終了する．
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            threshold = datetime.timedelta(minutes=5)
            if timestamp is not None and now - timestamp > threshold:
                raise RuntimeError(
                    '`archiver` service seems stuck for 5 minutes.')

            while True:
                fetch_time = datetime.datetime.now(
                    tz=datetime.timezone.utc)
                try:
                    logging.warning(
                        'Requesting the driver to refresh the page...')
                    driver.refresh()
                    logging.info('The driver has refreshed the page.')
                    break
                except TimeoutException:
                    logging.warning(
                        'Failed to refresh the page.  Trying again\
 requesting the driver to refresh the page after 1-minute sleep...')
                    time.sleep(60)
            canvas = _wait_for_page_to_present(driver)
            continue


if __name__ == '__main__':
    logging_.initialize(module_name='game_abstract_crawler',
                        service_name='crawler')

    for screenshot_path in _SCREENSHOT_PREFIX.glob('*.png'):
        screenshot_path.unlink()
        logging.info(f'Deleted an old screenshot `{screenshot_path}`.')

    while True:
        options = Options()
        options.headless = True
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')
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

        with Chrome(options=options) as driver:
            try:
                main(driver)
                break
            except Exception as e:
                _get_screenshot(driver, '99-エラー.png')
                logging.exception('Abort with an unhandled exception.')

        logging.info(
            f'''Sleep for {_CONFIG['retry_interval']} seconds.''')
        time.sleep(_CONFIG['retry_interval'])
