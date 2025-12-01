import pytest

from shark_metadata import delivery_data
from shark_metadata.delivery_data import get_static_metadata


@pytest.mark.parametrize(
    "given_config, given_keys, given_language",
    (
        (
            {"a": {"b": {"en": "value"}}},
            ["a", "b"],
            "sv",  # Language is missing
        ),
        (
            {"a": {"b": {"en": "value"}}},
            ["b", "b"],  # Outermost key is missing
            "en",
        ),
        (
            {"a": {"b": {"en": "value"}}},
            ["a", "c"],  # Innermost key is missing
            "en",
        ),
    ),
)
def test_default_behaviour_for_get_static_metadata_is_strict(
    monkeypatch, given_config, given_keys, given_language
):
    # Given a mocked config file
    monkeypatch.setattr(delivery_data, "_load_yaml", lambda *_: given_config)

    # When requesting a value with a specific language
    value = get_static_metadata("mocked_config", given_keys, language=given_language)

    # Then the expected value is returned
    assert value is None


@pytest.mark.parametrize(
    "given_config, given_keys, given_language, expected_value",
    (
        ({"a": {"b": {"en": "English", "sv": "Swedish"}}}, ["a", "b"], "en", "English"),
        ({"a": {"b": {"en": "English", "sv": "Swedish"}}}, ["a", "b"], "sv", "Swedish"),
    ),
)
def test_get_static_metadata_with_language(
    monkeypatch, given_config, given_keys, given_language, expected_value
):
    # Given a mocked config file
    monkeypatch.setattr(delivery_data, "_load_yaml", lambda *_: given_config)

    # When requesting a value with a specific language
    value = get_static_metadata("mocked_config", given_keys, language=given_language)

    # Then the expected value is returned
    assert value == expected_value


@pytest.mark.parametrize(
    "given_config, given_keys, given_language, expected_value",
    (
        (
            {"a": {"b": {"en": "English"}}},
            ["a", "b"],
            "sv",
            "English",
        ),  # Language fallback
        ({"a": {"b": {"en": "value"}}}, ["a", "c"], "en", "NA"),  # Missing key fallback
        (
            {"a": {"b": {"en": "value"}}},
            ["a", "b", "c"],
            "en",
            "NA",
        ),  # Missing level fallback
        (
            {"a": {"b": {"en": "value"}, "default": {"sv": "Swedish default"}}},
            ["a", "c"],
            "sv",
            "Swedish default",
        ),  # Default value, wrong key
        (
            {"a": {"b": {"en": "value"}, "default": {"en": "English default"}}},
            ["a", "c"],
            "sv",
            "English default",
        ),  # Default value, wrong key, missing language
    ),
)
def test_optional_fallback_behaviour_for_get_static_metadata(
    monkeypatch, given_config, given_keys, given_language, expected_value
):
    # Given a mocked config file
    monkeypatch.setattr(delivery_data, "_load_yaml", lambda *_: given_config)

    # When requesting a value with a specific language, using fallback mode
    value = get_static_metadata(
        "mocked_config", given_keys, language=given_language, fallback=True
    )

    # Then the expected value is returned
    assert value is expected_value
