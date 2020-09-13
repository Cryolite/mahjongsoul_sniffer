#!/usr/bin/env python3

import re
import datetime
import pathlib
import os.path
import hashlib
import os
import flask


app = flask.Flask(__name__)


_html_prefix = pathlib.Path('/usr/local/share/mahjongsoul-sniffer/game-abstract-crawler-monitor')


@app.route('/')
def top_page():
    return flask.send_from_directory(_html_prefix, 'index.html', mimetype='text/html')


@app.route('/js/<path:filename>')
def js(filename):
    return flask.send_from_directory(_html_prefix / 'js', filename,
                                     mimetype='text/javascript')


_log_prefix = pathlib.Path('/var/log/mahjongsoul-sniffer')


_game_abstract_crawler_log_prefix = _log_prefix / 'game-abstract-crawler'


@app.route('/screenshots.json')
def screenshots():
    screenshots = []
    for name in os.listdir(_game_abstract_crawler_log_prefix):
        if not name.endswith('.png'):
            continue

        path = _game_abstract_crawler_log_prefix / name

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
    return flask.send_from_directory(_game_abstract_crawler_log_prefix,
                                     filename, mimetype='image/png')


_sniffer_log_path = _log_prefix / 'sniffer.log'


@app.route('/sniffer.log')
def sniffer_log():
    if not _sniffer_log_path.exists():
        return ''

    if 'n' not in flask.request.args:
        n = -1
    else:
        n = int(flask.request.args['n'])
        if n < 0:
            n = 0

    queue = []
    with open(_sniffer_log_path) as f:
        for line in f:
            queue.append(line)
            if n != -1 and len(queue) > n:
                queue.pop(0)
    return ''.join(queue)


@app.route('/running')
def running():
    if not _sniffer_log_path.exists():
        flask.abort(404)
    if not _sniffer_log_path.is_file():
        flask.abort(404)

    last_activity_time = None
    with open(_sniffer_log_path) as sniffer_log:
        target_message = 'Sniffering WebSocket messages from/to\
 `.lq.Lobby.fetchGameLiveList`.'
        time_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
        for line in sniffer_log:
            if line.find(target_message) == -1:
                continue
            m = re.search(time_pattern, line)
            if m is None:
                flask.abort(404)
            last_activity_time = datetime.datetime.strptime(
                m.group(1), '%Y-%m-%d %H:%M:%S')

    if last_activity_time is None:
        flask.abort(404)

    now = datetime.datetime.now()
    if now - last_activity_time > datetime.timedelta(minutes=1):
        flask.abort(404)

    return 'Mahjongsoul Game Abstract Crawler is running.'
