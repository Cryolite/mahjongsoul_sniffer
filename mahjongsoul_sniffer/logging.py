# ruff: noqa: PLW0603

import logging
import logging.handlers
import pathlib

import mahjongsoul_sniffer.config as config_

_module_name = None
_service_name = None
_initialized = False


def initialize(
    *,
    module_name: str,
    service_name: str | None = None,
) -> None:
    global _module_name
    global _service_name
    global _initialized

    if _initialized:
        if module_name != _module_name:
            msg = f"""`initialize` is called with different module names:
Previous call: module_name = {_module_name}, service_name = {_service_name}
Current call: module_name = {module_name}, service_name = {service_name}"""
            raise RuntimeError(msg)
        if service_name != _service_name:
            msg = f"""`initialize` is called with different service names:
Previous call: module_name = {_module_name}, service_name = {_service_name}
Current call: module_name = {module_name}, service_name = {service_name}"""
            raise RuntimeError(msg)
        return

    config = config_.get(module_name)
    if service_name is not None:
        config = config[service_name]
    config = config["logging"]

    level = config["level"]

    handlers = []

    if "file" in config:
        file_config = config["file"]

        file_path = pathlib.Path(file_config["path"])
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if file_path.exists() and not file_path.is_file():
            msg = f"{file_path}: Not a file."
            raise RuntimeError(msg)

        file_max_bytes = file_config["max_bytes"]
        file_backup_count = file_config["backup_count"]

        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=file_max_bytes,
            backupCount=file_backup_count,
            delay=True,
        )
        handlers.append(file_handler)

    if "redis" in config:
        from mahjongsoul_sniffer.redis_log_handler import RedisLogHandler

        redis_handler = RedisLogHandler(
            module_name=module_name,
            service_name=service_name,
        )
        handlers.append(redis_handler)

    log_format = "%(asctime)s:%(filename)s:%(funcName)s:%(lineno)d:\
%(levelname)s: %(message)s"
    logging.basicConfig(format=log_format, level=level, handlers=handlers)

    _module_name = module_name
    _service_name = service_name
    _initialized = True
