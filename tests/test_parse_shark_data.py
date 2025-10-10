import shutil
from pathlib import Path

import polars as pl

from shark_metadata.delivery_data import DeliveryData


def _write_data_to_package_folder(
    given_shark_data: pl.DataFrame,
    given_delivery_note_data: dict[str, str],
    root_dir: Path,
) -> Path:
    package_path = root_dir / "SHARK_Phytoplankton"
    package_path.mkdir()
    given_shark_data.write_csv(package_path / "shark_data.txt", separator="\t")
    processed_data_path = package_path / "processed_data"
    processed_data_path.mkdir()
    given_shark_data.write_csv(processed_data_path / "data.txt", separator="\t")
    delivery_note_path = processed_data_path / "delivery_note.txt"
    delivery_note_path.write_text(
        "\n".join(f"{key}: {value}" for key, value in given_delivery_note_data.items())
    )
    return package_path


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
    given_delivery_note_data = {
        "datatyp": "Phytoplankton",
        "format": "Phytoplankton:PP_SMHI",
    }

    # Given path to package folder
    package_path = _write_data_to_package_folder(
        given_shark_data, given_delivery_note_data, tmp_path
    )

    # When parsing data using path
    metadata = DeliveryData.from_shark_package(package_path)

    # Then metadata holds data
    assert not metadata.data.is_empty()

    # And it is identical to the original data for the columns in the original data
    assert metadata.data[given_shark_data.columns].equals(given_shark_data)

    # And metadata holds delivery note
    assert metadata.delivery_note

    # And the values in the delivery note are identical to the original
    assert metadata.delivery_note["DTYPE"] == given_delivery_note_data["datatyp"]
    assert metadata.delivery_note["FORMAT"] == given_delivery_note_data["format"]


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

    given_delivery_note_data = {
        "datatyp": "Phytoplankton",
        "format": "Phytoplankton:PP_SMHI",
    }

    # Given path to package folder
    package_path = _write_data_to_package_folder(
        given_shark_data, given_delivery_note_data, tmp_path
    )

    zipped_package_path = Path(shutil.make_archive(package_path, "zip", package_path))

    # When parsing data using path
    metadata = DeliveryData.from_shark_package(zipped_package_path)

    # Then metadata holds data
    assert not metadata.data.is_empty()

    # And it is identical to the original data for the columns in the original data
    assert metadata.data[given_shark_data.columns].equals(given_shark_data)

    # And metadata holds delivery note
    assert metadata.delivery_note

    # And the values in the delivery note are identical to the original
    assert metadata.delivery_note["DTYPE"] == given_delivery_note_data["datatyp"]
    assert metadata.delivery_note["FORMAT"] == given_delivery_note_data["format"]
