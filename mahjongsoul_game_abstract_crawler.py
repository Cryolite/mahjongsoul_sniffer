#!/usr/bin/env python3

import datetime
import random
import pathlib
import os.path
import time
import getpass
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Chrome
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains


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


def _raise_if_gets_stuck() -> None:
    timestamp_file = pathlib.Path('output/fetch-game-live-list.timestamp')
    last_timestamp = int(os.path.getmtime(timestamp_file))
    now = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())

    if now - last_timestamp > 60:
        raise RefreshRequest()


def _after_login(fetch_time: datetime.datetime) -> None:
    timestamp_file = pathlib.Path('output/login.timestamp')
    login = False
    for i in range(60):
        time.sleep(1)
        if not timestamp_file.exists():
            continue
        if not timestamp_file.is_file():
            raise RuntimeError('`output/login.timestamp` is not a file.')
        timestamp = int(os.path.getmtime(timestamp_file))
        if timestamp >= int(fetch_time.timestamp()):
            login = True
            break
    if not login:
        raise RuntimeError('Failed to login.')
    time.sleep(5)

    driver.get_screenshot_as_file('output/ロビー.png')

    # 「観戦」ボタンをクリック
    click_canvas_within(driver, canvas, 491, 398, 51, 42)
    time.sleep(10)

    driver.get_screenshot_as_file('output/観戦.png')

    while True:
        # 部屋のプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 60, 88, 157, 30)
        time.sleep(1)

        # 部屋のプルダウンメニューから「金の間」を選択
        click_canvas_within(driver, canvas, 60, 119, 134, 30)
        time.sleep(15)

        # モードのプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 241, 88, 157, 30)
        time.sleep(1)

        # モードのプルダウンメニューから「4人東風戦」を選択
        click_canvas_within(driver, canvas, 241, 119, 134, 30)
        time.sleep(15)

        _raise_if_gets_stuck()

        driver.get_screenshot_as_file('output/金の間・四人東風戦.png')

        # モードのプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 241, 88, 157, 30)
        time.sleep(1)

        # モードのプルダウンメニューから「4人半荘戦」を選択
        click_canvas_within(driver, canvas, 241, 150, 134, 30)
        time.sleep(15)

        _raise_if_gets_stuck()

        driver.get_screenshot_as_file('output/金の間・四人半荘戦.png')

        # 部屋のプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 60, 88, 157, 30)
        time.sleep(1)

        # 部屋のプルダウンメニューから「玉の間」を選択
        click_canvas_within(driver, canvas, 60, 150, 134, 30)
        time.sleep(15)

        # モードのプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 241, 88, 157, 30)
        time.sleep(1)

        # モードのプルダウンメニューから「4人東風戦」を選択
        click_canvas_within(driver, canvas, 241, 119, 134, 30)
        time.sleep(15)

        _raise_if_gets_stuck()

        driver.get_screenshot_as_file('output/玉の間・四人東風戦.png')

        # モードのプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 241, 88, 157, 30)
        time.sleep(1)

        # モードのプルダウンメニューから「4人半荘戦」を選択
        click_canvas_within(driver, canvas, 241, 150, 134, 30)
        time.sleep(15)

        _raise_if_gets_stuck()

        driver.get_screenshot_as_file('output/玉の間・四人半荘戦.png')

        # 部屋のプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 60, 88, 157, 30)
        time.sleep(1)

        # 部屋のプルダウンメニューから「王座の間」を選択
        click_canvas_within(driver, canvas, 60, 182, 134, 30)
        time.sleep(15)

        # モードのプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 241, 88, 157, 30)
        time.sleep(1)

        # モードのプルダウンメニューから「4人東風戦」を選択
        click_canvas_within(driver, canvas, 241, 119, 134, 30)
        time.sleep(15)

        _raise_if_gets_stuck()

        driver.get_screenshot_as_file('output/王座の間・四人東風戦.png')

        # モードのプルダウンメニューをクリックして展開
        click_canvas_within(driver, canvas, 241, 88, 157, 30)
        time.sleep(1)

        # モードのプルダウンメニューから「4人半荘戦」を選択
        click_canvas_within(driver, canvas, 241, 150, 134, 30)
        time.sleep(15)

        _raise_if_gets_stuck()

        driver.get_screenshot_as_file('output/王座の間・四人半荘戦.png')


def main(driver: WebDriver) -> None:
    fetch_time = datetime.datetime.now(tz=datetime.timezone.utc)
    driver.get('https://game.mahjongsoul.com/')

    canvas = WebDriverWait(driver, 60).until(
        ec.visibility_of_element_located((By.ID, 'layaCanvas'))
    )
    # 「ログイン」ボタンをクリック
    click_canvas_within(driver, canvas, 540, 177, 167, 38)
    time.sleep(1)

    mail_address = input('メールアドレス: ')

    # 「メールアドレス」フォームに入力
    click_canvas_within(driver, canvas, 145, 154, 291, 30)
    ActionChains(driver).send_keys(mail_address).perform()
    time.sleep(1)

    # 「コードを受け取る」ボタンをクリック
    click_canvas_within(driver, canvas, 351, 206, 86, 36)
    time.sleep(1)

    # 「確認」ボタンをクリック
    click_canvas_within(driver, canvas, 378, 273, 60, 23)
    time.sleep(1)

    auth_code = getpass.getpass(prompt='認証コード: ',)

    # 「認証コード」フォームに入力
    click_canvas_within(driver, canvas, 144, 211, 196, 30)
    ActionChains(driver).send_keys(auth_code).perform()
    time.sleep(1)

    # 「ログイン」ボタンをクリック
    click_canvas_within(driver, canvas, 209, 293, 163, 37)

    while True:
        try:
            _after_login(fetch_time)
        except RefreshRequest:
            print('Refresh was requested.')
            fetch_time = datetime.datetime.now(tz=datetime.timezone.utc)
            driver.refresh()
            continue


if __name__ == '__main__':
    if not pathlib.Path('output').exists():
        raise RuntimeError('`output` directory does not exist.')
    if not pathlib.Path('output').is_dir():
        raise RuntimeError('`output` is not a directory.')

    options = Options()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=800,600')
    with Chrome(options=options) as driver:
        try:
            main(driver)
        except Exception as e:
            driver.get_screenshot_as_file('output/error.png')
            raise
