from pathlib import Path

import pytest
from sharkadm.config import DataTypeMapper

test_root = Path(__file__).parent
test_sharkadmconf = test_root / "test_sharkadmconf"


@pytest.fixture()
def mock_adm_config_paths(monkeypatch):
    config_paths = {
        "delivery_note_mapping": test_sharkadmconf / "delivery_note_mapping.txt",
    }
    monkeypatch.setattr(
        "sharkadm.config.adm_config_paths", lambda config: config_paths.get(config)
    )


@pytest.fixture()
def mock_nodccode_get_config_path(monkeypatch):
    config_paths = {"translate_codes.txt": test_sharkadmconf / "translate_codes.txt"}
    monkeypatch.setattr(
        "sharkadm.data.archive.delivery_note.nodc_codes.get_config_path",
        lambda config: config_paths.get(config),
    )


@pytest.fixture()
def mock_import_matrix_paths(monkeypatch):
    config_paths = {
        "phytoplankton": test_sharkadmconf / "import_matrix_phytoplankton.txt"
    }

    monkeypatch.setattr(
        "sharkadm.config.import_matrix_paths",
        config_paths,
    )


@pytest.fixture()
def mock_mapper_data_type_to_internal(monkeypatch):
    monkeypatch.setattr(
        "sharkadm.data.zip_archive.zip_archive_data_holder.mapper_data_type_to_internal",
        DataTypeMapper(test_sharkadmconf / "mapper_data_type_to_internal.yaml"),
    )
