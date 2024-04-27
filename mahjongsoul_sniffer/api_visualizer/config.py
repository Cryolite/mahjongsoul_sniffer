import pathlib

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


CONFIG_SCHEMA = {
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


CONFIG_FILE_PATH = pathlib.Path("api-visualizer/config.yaml")
