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


_S3_CONFIG_SCHEMA = {
    "type": "object",
    "required": [
        "bucket_name",
        "game_abstract_key_prefixes",
        "game_detail_key_prefix",
    ],
    "properties": {
        "bucket_name": {
            "type": "string",
        },
        "game_abstract_key_prefixes": {
            "type": "array",
            "minItems": 3,
            "maxItems": 3,
            "items": {
                "type": "string",
            },
            "additionalItems": False,
        },
        "game_detail_key_prefix": {
            "type": "string",
        },
    },
    "additionalProperties": False,
}


_GOOGLEAPI_CONFIG_SCHEMA = {
    "type": "object",
    "required": [
        "client_id",
        "client_secret",
    ],
    "properties": {
        "client_id": {
            "type": "string",
        },
        "client_secret": {
            "type": "string",
        },
    },
    "additionalProperties": False,
}


_SPREADSHEET_CONFIG_SCHEMA = {
    "type": "object",
    "required": [
        "id",
        "sheet_title",
    ],
    "properties": {
        "id": {
            "type": "string",
        },
        "sheet_title": {
            "type": "string",
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


_MAIN_CONFIG_SCHEMA = {
    "type": "object",
    "required": [
        "logging",
    ],
    "properties": {
        "logging": _LOGGING_CONFIG_SCHEMA,
    },
    "additionalProperties": False,
}


CONFIG_SCHEMA = {
    "type": "object",
    "required": [
        "redis",
        "interval",
        "s3",
        "googleapi",
        "spreadsheet",
        "main",
    ],
    "properties": {
        "redis": _REDIS_CONFIG_SCHEMA,
        "interval": {
            "type": "integer",
            "minimum": 0,
        },
        "s3": _S3_CONFIG_SCHEMA,
        "googleapi": _GOOGLEAPI_CONFIG_SCHEMA,
        "spreadsheet": _SPREADSHEET_CONFIG_SCHEMA,
        "main": _MAIN_CONFIG_SCHEMA,
    },
    "additionalProperties": False,
}


CONFIG_FILE_PATH = pathlib.Path("crawler-batch/config.yaml")
