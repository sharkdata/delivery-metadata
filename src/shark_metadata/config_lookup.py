from importlib import resources
from pathlib import Path

from shark_metadata.delivery_data import get_static_metadata

_file_map = {
    "title": ("titles", "titles"),
    "abstract": ("abstract", "abstract"),
}


def get_reference(key: str, language: str = "en"):
    file_key, *keys = key.split("-")
    if file_parts := _file_map.get(file_key):
        filename, root_key = file_parts
        return get_static_metadata(filename, [root_key, *keys], language=language)
    return None


def get_config_directory() -> Path:
    return Path(resources.files(__package__)) / "metadata_config"
