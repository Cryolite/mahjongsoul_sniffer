import os.path
import logging
import sys
import inspect

# This file is executed by `mitmdump' with `execfile'. Therefore, in
# order to import submodules under the directory where this file exists,
# we need some tricks. See http://stackoverflow.com/questions/3718657
# for the details of the tricks used in the following lines.
THIS_FILENAME = inspect.getframeinfo(inspect.currentframe()).filename
THIS_DIR_PATH = os.path.dirname(os.path.abspath(THIS_FILENAME))
sys.path.append(THIS_DIR_PATH)
import mahjongsoul_sniffer.logging as logging_
from mahjongsoul_sniffer.redis_mirroring import RedisMirroring


logging_.initialize(
    module_name='game_detail_crawler', service_name='sniffer')


_REDIS_MIRRORING_CONFIG = {
    'websocket': {
        '.lq.Lobby.loginBeat': {
            'request_direction': 'outbound',
            'action': {
                'command': 'SET',
                'key': 'login-beat'
            }
        },
        '.lq.Lobby.fetchGameRecord': {
            'request_direction': 'outbound',
            'action': {
                'command': 'SET',
                'key': 'game-detail'
            }
        }
    }
}


redis_mirroring = RedisMirroring(
    module_name='game_detail_crawler', config=_REDIS_MIRRORING_CONFIG)


def websocket_message(flow) -> None:
    try:
        redis_mirroring.on_websocket_message(flow)
    except Exception as e:
        logging.exception(
            '`RedisMirroring.on_websocket_message` threw an exception.')
