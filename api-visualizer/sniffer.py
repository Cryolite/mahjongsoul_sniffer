#!/usr/bin/env python3
# ruff: noqa: E402, INP001
import inspect
import logging
import sys
from pathlib import Path

from mitmproxy.http import HTTPFlow

# This file is executed by `mitmdump' with `execfile'. Therefore, in
# order to import submodules under the directory where this file exists,
# we need some tricks. See http://stackoverflow.com/questions/3718657
# for the details of the tricks used in the following lines.
_THIS_FILENAME = inspect.getframeinfo(inspect.currentframe()).filename
_THIS_DIR_PATH = Path(_THIS_FILENAME).resolve().parent
sys.path.append(str(_THIS_DIR_PATH))

import mahjongsoul_sniffer.logging as logging_
from mahjongsoul_sniffer import mahjongsoul_pb2
from mahjongsoul_sniffer.redis_mirroring import RedisMirroring

logging_.initialize(module_name="api_visualizer", service_name="sniffer")


_METHOD_NAMES = [
    "." + mdesc.full_name
    for sdesc in mahjongsoul_pb2.DESCRIPTOR.services_by_name.values()
    for mdesc in sdesc.methods
]


_MESSAGE_TYPE_NAMES = [
    "." + tdesc.full_name
    for tdesc in mahjongsoul_pb2.DESCRIPTOR.message_types_by_name.values()
]


_REDIS_MIRRORING_CONFIG: dict[str, dict] = {"websocket": {}}
for mname in _METHOD_NAMES:
    _REDIS_MIRRORING_CONFIG["websocket"][mname] = {
        "request_direction": "both",
        "action": {"command": "RPUSH", "key": "api-call-queue"},
    }
for tname in _MESSAGE_TYPE_NAMES:
    _REDIS_MIRRORING_CONFIG["websocket"][tname] = {
        "request_direction": "both",
        "action": {"command": "RPUSH", "key": "api-call-queue"},
    }


_redis_mirroring = RedisMirroring(
    module_name="api_visualizer",
    config=_REDIS_MIRRORING_CONFIG,
)


def websocket_message(flow: HTTPFlow) -> None:
    if (websocket_data := flow.websocket) is None:
        msg = "HTTP flow does not contain WebSocket data."
        raise RuntimeError(msg)
    try:
        _redis_mirroring.on_websocket_message(websocket_data)
    except Exception:
        logging.exception(
            "`RedisMirroring.on_websocket_message` threw an exception.",
        )
