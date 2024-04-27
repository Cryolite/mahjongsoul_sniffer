#!/usr/bin/env python3

import importlib
import pathlib
from functools import cache

import jsonschema
import yaml


def _load(file_path: pathlib.Path, schema: dict[str, object]) -> dict:
    if not file_path.exists():
        msg = f"{file_path}: File does not exist."
        raise RuntimeError(msg)
    if not file_path.is_file():
        msg = f"{file_path}: Not a file."
        raise RuntimeError(msg)

    with file_path.open() as config_file:
        config = yaml.safe_load(config_file)

    jsonschema.validate(instance=config, schema=schema)

    return config


@cache
def get(module_name: str) -> dict:
    config_module_path = f"mahjongsoul_sniffer.{module_name}.config"
    config_module = importlib.import_module(config_module_path)
    return _load(config_module.CONFIG_FILE_PATH, config_module.CONFIG_SCHEMA)
