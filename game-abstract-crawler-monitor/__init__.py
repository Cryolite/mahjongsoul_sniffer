#!/usr/bin/env python3

import datetime
import pathlib
import os.path
import hashlib
import os
import flask
import mahjongsoul_sniffer.sniffer


app = flask.Flask(__name__)


_html_prefix = pathlib.Path(
    '/usr/local/share/mahjongsoul-sniffer/game-abstract-crawler-monitor')


@app.route('/')
def top_page():
    return flask.send_from_directory(_html_prefix, 'index.html',
                                     mimetype='text/html')


@app.route('/js/<path:filename>')
def js(filename):
    return flask.send_from_directory(_html_prefix / 'js', filename,
                                     mimetype='text/javascript')


_LOG_PREFIX = pathlib.Path('/var/log/mahjongsoul-sniffer')


_CRAWLER_LOG_PREFIX = _LOG_PREFIX / 'game-abstract-crawler'


@app.route('/screenshots.json')
def screenshots():
    screenshots = []
    for name in os.listdir(_CRAWLER_LOG_PREFIX):
        if not name.endswith('.png'):
            continue

        path = _CRAWLER_LOG_PREFIX / name

        hasher = hashlib.sha512()
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(65536)
                if len(chunk) == 0:
                    break
                hasher.update(chunk)
        digest = hasher.hexdigest()

        mtime = int(os.path.getmtime(path))

        screenshots.append({
            'name': name,
            'digest': digest,
            'timestamp': mtime
        })

    screenshots.sort(key=lambda e: e['name'])
    return flask.json.jsonify(screenshots)


@app.route('/screenshot/<path:filename>')
def screenshot(filename):
    return flask.send_from_directory(_CRAWLER_LOG_PREFIX,
                                     filename, mimetype='image/png')


@app.route('/sniffer.log')
def sniffer_log():
    redis_client = mahjongsoul_sniffer.sniffer.RedisClient()
    records = redis_client.get_all_log_records('log.sniffer')
    return '\n'.join(records)


@app.route('/archiver.log')
def archiver_log():
    redis_client = mahjongsoul_sniffer.sniffer.RedisClient()
    records = redis_client.get_all_log_records('log.archiver')
    return '\n'.join(records)


@app.route('/crawler.log')
def crawler_log():
    redis_client = mahjongsoul_sniffer.sniffer.RedisClient()
    records = redis_client.get_all_log_records('log.crawler')
    return '\n'.join(records)


@app.route('/running')
def running():
    redis_client = mahjongsoul_sniffer.sniffer.RedisClient()
    timestamp = redis_client.get_timestamp('archiver.heartbeat')

    if timestamp is None:
        flask.abort(404)

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    threshold = datetime.timedelta(minutes=5)
    if now - timestamp > threshold:
        flask.abort(404)

    return 'MahjongSoul Game Abstract Crawler is running.'
