from shark_metadata.delivery_data import restructure_by_language


def test_restructure_by_language():
    # Given a dictionary with language nodes
    given_metadata = {}

    # Given a key path
    given_key_path = ("A",)

    # Given a language
    given_language = "sv"

    # Given there is a translation for the key
    given_value = "Lorem Ipsum"

    metadata_pointer = given_metadata
    for key in given_key_path:
        metadata_pointer[key] = {}
        metadata_pointer = metadata_pointer[key]
    metadata_pointer[given_language] = given_value

    # When restructuring the dictionary
    restructured_metadata = restructure_by_language(given_metadata)

    # Then the given language is on the highest level
    assert given_language in restructured_metadata

    # Then the key directly leads to the text in the specified language
    metadata_pointer = restructured_metadata[given_language]
    for key in given_key_path:
        metadata_pointer = metadata_pointer[key]

    assert given_language not in metadata_pointer
    assert metadata_pointer == given_value
