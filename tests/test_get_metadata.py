import json

from shark_metadata.delivery_data import get_static_metadata


def test_get_default_when_missing_given_key():
    result = get_static_metadata(
        "monitoring_program", ["coast"], lang="sv"
    )
    assert not result == "NA"


def test_get_none_when_missing_key():
    result = get_static_metadata("monitoring_program", [], lang="sv")
    assert isinstance(result, str)


def test_get_none_when_wrong_key():
    result = get_static_metadata("monitoring_programxxx", [], lang="sv")
    assert isinstance(result, str)
