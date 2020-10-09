#!/usr/bin/env python3

import datetime
import pathlib
import os.path
import hashlib
import os
import flask
import mahjongsoul_sniffer.redis as redis_


app = flask.Flask(__name__)


_HTML_PREFIX = pathlib.Path(
    '/srv/mahjongsoul-sniffer/game-detail-crawler')


_LOG_PREFIX = pathlib.Path(
    '/var/log/mahjongsoul-sniffer/game-detail-crawler')


_redis = redis_.Redis(module_name='game_detail_crawler')


@app.route('/')
def top_page():
    return flask.send_from_directory(
        _HTML_PREFIX, 'index.html', mimetype='text/html')


@app.route('/js/<path:filename>')
def js(filename):
    return flask.send_from_directory(
        _HTML_PREFIX / 'js', filename, mimetype='text/javascript')


@app.route('/screenshots.json')
def screenshots():
    if _LOG_PREFIX.exists() and not _LOG_PREFIX.is_dir():
        flask.abort(404, description=f'{_LOG_PREFIX}: Not a directory.')

    screenshots = []

    if not _LOG_PREFIX.exists():
        return flask.json.jsonify(screenshots)

    for name in os.listdir(_LOG_PREFIX):
        if not name.endswith('.png'):
            continue

        path = _LOG_PREFIX / name

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
    return flask.send_from_directory(
        _LOG_PREFIX, filename, mimetype='image/png')


@app.route('/log.json')
def log_json():
    sniffer_records = _redis.get_all_log_records('log.sniffer')
    archiver_records = _redis.get_all_log_records('log.archiver')
    crawler_records = _redis.get_all_log_records('log.crawler')
    return flask.json.jsonify({
        'sniffer': sniffer_records,
        'archiver': archiver_records,
        'crawler': crawler_records
    })


@app.route('/sniffer.log')
def sniffer_log():
    return flask.send_from_directory(
        '/var/log/mahjongsoul-sniffer/game-detail-crawler',
        'sniffer.log', mimetype='text/plain')


@app.route('/archiver.log')
def archiver_log():
    return flask.send_from_directory(
        '/var/log/mahjongsoul-sniffer/game-detail-crawler',
        'archiver.log', mimetype='text/plain')


@app.route('/crawler.log')
def crawler_log():
    return flask.send_from_directory(
        '/var/log/mahjongsoul-sniffer/game-detail-crawler',
        'crawler.log', mimetype='text/plain')


@app.route('/running')
def running():
    timestamp = _redis.get_timestamp('archiver.heartbeat')

    if timestamp is None:
        flask.abort(404)

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    threshold = datetime.timedelta(minutes=5)
    if now - timestamp > threshold:
        flask.abort(404)

    return 'MahjongSoul Game Detail Crawler is running.'
