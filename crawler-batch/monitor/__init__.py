#!/usr/bin/env python3

import datetime
import flask
import mahjongsoul_sniffer.redis as redis_


app = flask.Flask(__name__)


_redis = redis_.Redis(module_name='crawler_batch')


@app.route('/running')
def running():
    timestamp = _redis.get_timestamp('main.heartbeat')

    if timestamp is None:
        flask.abort(404)

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    threshold = datetime.timedelta(hours=6)
    if now - timestamp > threshold:
        flask.abort(404)

    response = flask.make_response(
        'MahjongSoul Crawler Batch is running.')
    response.cache_control.max_age = 0
    return response
