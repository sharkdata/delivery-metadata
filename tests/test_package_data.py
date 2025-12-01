import shutil
from pathlib import Path

import polars as pl

from shark_metadata.delivery_package import DeliveryPackage


def _write_data_to_package_folder(
    given_shark_data: pl.DataFrame,
    given_delivery_note_data: dict[str, str],
    given_version_string: str,
    root_dir: Path,
) -> Path:
    package_path = root_dir / f"SHARK_Phytoplankton_{given_version_string}"
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

    # Given a version string
    given_version_string = "20251127"

    # Given path to delivery package directory
    package_path = _write_data_to_package_folder(
        given_shark_data, given_delivery_note_data, given_version_string, tmp_path
    )

    # When parsing data using the path
    delivery_package = DeliveryPackage.from_directory(package_path)

    # Then the object holds data
    assert not delivery_package.data.is_empty()

    # And it is identical to the original data for the columns in the original data
    assert delivery_package.data[given_shark_data.columns].equals(given_shark_data)

    # And the object holds a delivery note
    assert delivery_package.delivery_note

    # And the values in the delivery note are identical to the original
    assert (
        delivery_package.delivery_note["datatyp"] == given_delivery_note_data["datatyp"]
    )
    assert delivery_package.delivery_note["format"] == given_delivery_note_data["format"]

    # And the version is parsed from the directory name
    assert delivery_package.version == given_version_string


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

    # Given a version string
    given_version_string = "20251127"

    # Given path to delivery package directory
    package_path = _write_data_to_package_folder(
        given_shark_data, given_delivery_note_data, given_version_string, tmp_path
    )

    zipped_package_path = Path(shutil.make_archive(package_path, "zip", package_path))

    # When parsing data using path
    delivery_package = DeliveryPackage.from_zip(zipped_package_path)

    # Then the object holds data
    assert not delivery_package.data.is_empty()

    # And it is identical to the original data for the columns in the original data
    assert delivery_package.data[given_shark_data.columns].equals(given_shark_data)

    # And the object holds a delivery note
    assert delivery_package.delivery_note

    # And the values in the delivery note are identical to the original
    assert (
        delivery_package.delivery_note["datatyp"] == given_delivery_note_data["datatyp"]
    )
    assert delivery_package.delivery_note["format"] == given_delivery_note_data["format"]
