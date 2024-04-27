import pathlib

import jsonschema
import yaml


def load_config(file_path: pathlib.Path, schema: dict[str, object]) -> dict:
    if not file_path.exists():
        msg = f"{file_path}: File does not exist."
        raise RuntimeError(msg)
    if not file_path.is_file():
        msg = f"{file_path}: Not a file."
        raise RuntimeError(msg)

    with file_path.open() as config_file:
        config = yaml.load(config_file, Loader=yaml.Loader)

    jsonschema.validate(instance=config, schema=schema)

    return config
