import pathlib
from functools import cache

import jsonschema
import yaml

_REDIS_CONFIG_SCHEMA = {
    "type": "object",
    "required": [
        "host",
        "port",
    ],
    "properties": {
        "host": {
            "type": "string",
        },
        "port": {
            "type": "integer",
            "minimum": 1,
            "maximum": 65535,
        },
    },
    "additionalProperties": False,
}


_LOGGING_CONFIG_SCHEMA = {
    "type": "object",
    "required": [
        "level",
        "file",
    ],
    "properties": {
        "level": {
            "enum": [
                "DEBUG",
                "INFO",
                "WARNING",
                "ERROR",
                "CRITICAL",
            ],
        },
        "file": {
            "type": "object",
            "required": [
                "path",
                "max_bytes",
                "backup_count",
            ],
            "properties": {
                "path": {
                    "type": "string",
                },
                "max_bytes": {
                    "type": "integer",
                    "minimum": 0,
                },
                "backup_count": {
                    "type": "integer",
                    "minimum": 0,
                },
            },
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
}


_CONFIG_SCHEMA = {
    "type": "object",
    "required": [
        "redis",
        "sniffer",
        "web_server",
    ],
    "properties": {
        "redis": _REDIS_CONFIG_SCHEMA,
        "sniffer": {
            "type": "object",
            "required": [
                "logging",
            ],
            "properties": {
                "logging": _LOGGING_CONFIG_SCHEMA,
            },
            "additionalProperties": False,
        },
        "web_server": {
            "type": "object",
            "required": [
                "logging",
            ],
            "properties": {
                "logging": _LOGGING_CONFIG_SCHEMA,
            },
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
}


_CONFIG_FILE_PATH = pathlib.Path("api-visualizer/config.yaml")


@cache
def get() -> dict:
    if not _CONFIG_FILE_PATH.exists():
        msg = f"{_CONFIG_FILE_PATH}: File does not exist."
        raise RuntimeError(msg)
    if not _CONFIG_FILE_PATH.is_file():
        msg = f"{_CONFIG_FILE_PATH}: Not a file."
        raise RuntimeError(msg)

    with _CONFIG_FILE_PATH.open() as config_file:
        config = yaml.load(config_file, Loader=yaml.Loader)

    jsonschema.validate(instance=config, schema=_CONFIG_SCHEMA)

    return config
