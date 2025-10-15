import json

from shark_metadata.delivery_data import _load_all_yaml, get_static_metadata


def test_create_combined_dict():
    result = _load_all_yaml()
    assert isinstance(result, dict)


def test_get_default_when_missing_given_key():
    result = get_static_metadata(
        _load_all_yaml(), ["monitoring_program", "coast"], lang="sv"
    )
    assert isinstance(result, str)


def test_get_none_when_missing_key():
    result = get_static_metadata(_load_all_yaml(), ["monitoring_program"], lang="sv")
    assert result is None


def test_get_none_when_wrong_key():
    result = get_static_metadata(_load_all_yaml(), ["monitoring_programxxxx"], lang="sv")
    assert result is None
