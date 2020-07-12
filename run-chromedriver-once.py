#!/usr/bin/env python3

from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Chrome


if __name__ == '__main__':
    options = Options()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--window-size=800,600')
    with Chrome(options=options) as driver:
        driver.get('https://www.google.com/')
