import inspect
import sys
import os.path
import mitmproxy.websocket

# This file is executed by `mitmdump' with `execfile'. Therefore, in order to
# import submodules under the directory where this file exists, we need some
# tricks. See http://stackoverflow.com/questions/3718657 for the details of
# the tricks used in the following lines.
THIS_FILENAME = inspect.getframeinfo(inspect.currentframe()).filename
THIS_DIR_PATH = os.path.dirname(os.path.abspath(THIS_FILENAME))
sys.path.append(THIS_DIR_PATH)
import mahjongsoul_sniffer.config
from mahjongsoul_sniffer.sniffer.redis_mirroring import RedisMirroring


mahjongsoul_sniffer.config.initialize_logging('sniffer')


_REDIS_MIRRORING_CONFIG = {
    'websocket': {
        '.lq.Lobby.loginBeat': {
            'request_direction': 'outbound',
            'action': {
                'command': 'SET',
                'key': 'login-beat'
            }
        },
        '.lq.Lobby.fetchGameLiveList': {
            'request_direction': 'outbound',
            'action': {
                'command': 'RPUSH',
                'key': 'game-abstract-list'
            }
        }
    }
}


redis_mirroring = RedisMirroring(_REDIS_MIRRORING_CONFIG)


def websocket_message(flow: mitmproxy.websocket.WebSocketFlow) -> None:
    redis_mirroring.on_websocket_message(flow)
