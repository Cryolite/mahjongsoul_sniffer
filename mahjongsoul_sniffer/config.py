import importlib


def get(module_name: str) -> dict:
    config_module_path = f"mahjongsoul_sniffer.{module_name}.config"
    config_module = importlib.import_module(config_module_path)
    return config_module.get()
