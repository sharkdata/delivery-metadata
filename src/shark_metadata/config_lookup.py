from shark_metadata.delivery_data import get_static_metadata

_file_map = {
    "title": ("dcat_ap_se", "titles", "titles"),
    "abstract": ("dcat_ap_se", "abstract", "abstract"),
}


def get_reference(key: str, language: str = "en"):
    file_key, *keys = key.split("-")
    if file_parts := _file_map.get(file_key):
        directory, filename, root_key = file_parts
        return get_static_metadata(
            filename, [root_key, *keys], language=language, directory=directory
        )
    return None
