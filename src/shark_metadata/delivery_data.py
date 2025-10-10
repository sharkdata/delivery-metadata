from pathlib import Path
from typing import Callable, Self

import polars as pl
from sharkadm.data import get_polars_data_holder


def _apply_on_column(function: Callable, column: str, dataframe: pl.DataFrame):
    if column not in dataframe.columns:
        return None

    return function(dataframe[column])


class DeliveryData:
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

    def __init__(
        self,
        data: pl.DataFrame | None = None,
        delivery_note: dict | None = None,
        source: str = "",
    ):
        self._data = pl.DataFrame() if data is None else data
        self._delivery_note = delivery_note or {}
        self._source = source

    @property
    def data(self):
        return self._data

    @property
    def delivery_note(self):
        return self._delivery_note

    @property
    def fields(self):
        return self._fields

    def generate_metadata(self):
        print("\n".join(sorted(self._data.columns)))
        return {
            "datatype": self._delivery_note.get("DTYPE"),
            "abstract": None,
            "description": None,
            "dataset_filename": self._source,
            "discipline": None,
            "measuring_area_type": None,
            "coordinate_system": None,
            "platform_class": None,
            "access_constraints": None,
            "min_year": _apply_on_column(min, "visit_year", self._data),
            "max_year": _apply_on_column(max, "visit_year", self._data),
            "min_date": _apply_on_column(min, "sample_date", self._data),
            "max_date": _apply_on_column(max, "sample_date", self._data),
            "min_longitude_dd": _apply_on_column(min, "sample_longitude_dd", self._data),
            "max_longitude_dd": _apply_on_column(max, "sample_longitude_dd", self._data),
            "min_latitude_dd": _apply_on_column(min, "sample_latitude_dd", self._data),
            "max_latitude_dd": _apply_on_column(max, "sample_latitude_dd", self._data),
            "taxonomic_coverage": None,
            "originator": None,
            "contact": None,
            "orderer": None,
            "data_holding_centre": None,
            "data distributor": None,
            "database_reference": None,
            "internet_access": None,
            "address": None,
            "postal_code": None,
            "city": None,
            "phone": None,
            "email": None,
            "citation": None,
        }

    @classmethod
    def from_shark_package(cls, package_path: Path) -> Self:
        sharkadm_dataholder = get_polars_data_holder(package_path)
        return cls(
            data=sharkadm_dataholder.data,
            delivery_note=sharkadm_dataholder.delivery_note.data,
            source=package_path.name,
        )
