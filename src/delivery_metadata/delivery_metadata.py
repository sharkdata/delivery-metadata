from pathlib import Path
from typing import Self

from sharkadm.data import PolarsDataHolder, get_polars_data_holder


class DeliveryMetadata:
    _fields = (
        "datatype",
        "abstract",
        "description",
        "dataset_filename",
        "discipline",
        "measuring_area_type",
        "coordinate_system",
        "platform_class",
        "access_constraints",
        "min_year",
        "max_year",
        "min_date",
        "max_date",
        "min_longitude_dd",
        "max_longitude_dd",
        "min_latitude_dd",
        "max_latitude_dd",
        "taxonomic_coverage",
        "originator",
        "contact",
        "orderer",
        "data_holding_centre",
        "data distributor",
        "database_reference",
        "internet_access",
        "address",
        "postal_code",
        "city",
        "phone",
        "email",
        "citation",
    )

    def __init__(self, data_holder: PolarsDataHolder | None = None):
        self._data_holder = data_holder

    @property
    def data(self):
        return self._data_holder.data

    @property
    def delivery_note(self):
        return self._data_holder.delivery_note.data

    @property
    def fields(self):
        return self._fields

    @classmethod
    def from_shark_package(cls, package_path: Path) -> Self:
        sharkadm_dataholder = get_polars_data_holder(package_path)
        return cls(data_holder=sharkadm_dataholder)
