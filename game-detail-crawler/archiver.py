#!/usr/bin/env python3

import datetime
import os
import logging
import mahjongsoul_sniffer.logging as logging_
import mahjongsoul_sniffer.redis as redis_
import mahjongsoul_sniffer.game_detail as game_detail_
import mahjongsoul_sniffer.s3 as s3_


def main():
    redis = redis_.Redis(module_name='game_detail_crawler')
    s3_bucket = s3_.Bucket(module_name='game_detail_crawler')

    while True:
        message = redis.blpop_websocket_message('game-detail-list')
        redis.set_timestamp('archiver.heartbeat')
        fetch_time = datetime.datetime.now(tz=datetime.timezone.utc)
        if message['request_direction'] != 'outbound':
            raise RuntimeError('An outbound WebSocket message is\
 expected, but got an inbound one.')

        message = message['response']
        try:
            if 'MAHJONGSOUL_SNIFFER_DISABLE_GAME_DETAIL_VALIDATION' not in os.environ or os.environ['MAHJONGSOUL_SNIFFER_DISABLE_GAME_DETAIL_VALIDATION'] == '':
                game_detail_.validate(message)
        except game_detail_.ValidationError as e:
            raise

        s3_bucket.put_game_detail(message)

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        elapsed_time = now - fetch_time
        logging.info(
            f'Elapsed time to validate the message: {elapsed_time}')


if __name__ == '__main__':
    try:
        logging_.initialize(
            module_name='game_detail_crawler', service_name='archiver')
        main()
    except Exception as e:
        logging.exception('Abort with an unhandled exception.')
        raise
