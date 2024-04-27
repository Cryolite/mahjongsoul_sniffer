import importlib
from functools import cache

from mahjongsoul_sniffer.config_loader import load_config


@cache
def get(module_name: str) -> dict:
    config_module_path = f"mahjongsoul_sniffer.{module_name}.config"
    config_module = importlib.import_module(config_module_path)
    return load_config(
        config_module.CONFIG_FILE_PATH,
        config_module.CONFIG_SCHEMA,
    )
