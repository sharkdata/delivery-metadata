import shutil
from pathlib import Path

import polars as pl

from delivery_metadata import DeliveryMetadata


def test_parse_unpacked_folder(
    tmp_path,
    mock_adm_config_paths,
    mock_nodccode_get_config_path,
    mock_import_matrix_paths,
):
    # Given data for a SHARK package
    given_shark_data = pl.DataFrame(
        {
            "ColumnA": ["1", "2", "3"],
            "ColumnB": ["2.1", "2.2", "2.3"],
        }
    )
    given_delivery_note = """
datatyp: Phytoplankton
format: Phytoplankton:PP_SMHI
"""

    # Given path to data
    package_path = tmp_path / "SHARK_Phytoplankton"
    package_path.mkdir()
    processed_data_path = package_path / "processed_data"
    processed_data_path.mkdir()
    given_shark_data.write_csv(processed_data_path / "data.txt", separator="\t")
    delivery_note_path = processed_data_path / "delivery_note.txt"
    delivery_note_path.write_text(given_delivery_note)

    # When parsing data using path
    metadata = DeliveryMetadata.from_shark_package(package_path)

    # Then metadata holds data
    assert not metadata.data.is_empty()

    # And it is identical to the original data for the columns in the original data
    assert metadata.data[given_shark_data.columns].equals(given_shark_data)


def test_parse_zipped_folder(
    tmp_path,
    mock_adm_config_paths,
    mock_nodccode_get_config_path,
    mock_import_matrix_paths,
    mock_mapper_data_type_to_internal,
):
    # Given data for a SHARK package
    given_shark_data = pl.DataFrame(
        {
            "ColumnA": ["1", "2", "3"],
            "ColumnB": ["2.1", "2.2", "2.3"],
        }
    )
    given_delivery_note = """
datatyp: Phytoplankton
format: Phytoplankton:PP_SMHI
"""

    # Given path to data
    package_path = tmp_path / "SHARK_Phytoplankton"
    package_path.mkdir()
    given_shark_data.write_csv(package_path / "shark_data.txt", separator="\t")

    processed_data_path = package_path / "processed_data"
    processed_data_path.mkdir()
    delivery_note_path = processed_data_path / "delivery_note.txt"
    delivery_note_path.write_text(given_delivery_note)

    zipped_package_path = Path(shutil.make_archive(package_path, "zip", package_path))

    # When parsing data using path
    metadata = DeliveryMetadata.from_shark_package(zipped_package_path)

    # Then metadata holds data
    assert not metadata.data.is_empty()

    # And it is identical to the original data for the columns in the original data
    assert metadata.data[given_shark_data.columns].equals(given_shark_data)
