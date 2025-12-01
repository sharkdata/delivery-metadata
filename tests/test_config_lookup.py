import pytest

from shark_metadata import config_lookup


@pytest.mark.parametrize(
    "given_key, given_language, expected_result",
    (
        (
            "title-NAT-phytoplankton",
            "en",
            "SHARK - National marine environmental monitoring of Phytoplankton in Sweden "
            "since 1983.",
        ),
        (
            "title-NAT-phytoplankton",
            "sv",
            "SHARK - Nationell marin miljöövervakning av växtplankton i Sverige "
            "sedan 1983.",
        ),
    ),
)
def test_get_reference(given_key, given_language, expected_result):
    text = config_lookup.get_reference(given_key, given_language)
    assert text == expected_result
