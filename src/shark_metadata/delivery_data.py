from functools import cache
from importlib import resources
from pathlib import Path
from typing import Callable, Self

import polars as pl
import yaml
from nodc_codes import get_translate_codes_object
from sharkadm.data import get_polars_data_holder


def _apply_on_column(function: Callable, column: str, dataframe: pl.DataFrame):
    if column not in dataframe.columns:
        return None

    return function(dataframe[column])


@cache
def _load_yaml(filename: str) -> dict:
    resource = Path(resources.files(__package__)) / "metadata_config" / f"{filename}.yaml"
    if Path(resource).exists():
        with open(resource, encoding="utf-8") as f:
            return yaml.safe_load(f)
    else:
        return {}


def get_static_metadata(filename: str, keys: list, lang: str = "en"):
    metadata = _load_yaml(filename)
    for key in keys:
        if not isinstance(metadata, dict):
            return "NA"
        metadata = metadata.get(key) or metadata.get("default")
        if metadata is None:
            return "NA"
    if not isinstance(metadata, dict):
        return "NA"
    return metadata.get(lang, "NA")


class DeliveryData:
    _fields = (
        "datatype",
        "monitoring_program",
        "method_description",
        "dataset_filename",
        "keywords",
        "measuring_area_type",
        "coordinate_system",
        "platform_class",
        "license",
        "min_year",
        "max_year",
        "min_date",
        "max_date",
        "min_longitude_dd",
        "max_longitude_dd",
        "min_latitude_dd",
        "max_latitude_dd",
        "stations",
        "parameters",
        "taxonomic_coverage",
        "originator",
        "orderer",
        "data_holding_centre",
        "database_reference",
        "internet_access",
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
    def datatype(self):
        return self.delivery_note.get("DTYPE", "")

    @property
    def monitoring_program(self):
        return self.delivery_note.get("MPROG") or self.delivery_note.get(
            "monitoring_program_code"
        )

    @property
    def originator(self):
        return self.delivery_note.get("RLABO", "")

    @property
    def fields(self):
        return self._fields

    def generate_metadata(self):
        print("\n".join(sorted(self._data.columns)))
        print(self.delivery_note)
        return {
            "datatype": get_translate_codes_object().get_english_name(
                "delivery_datatype", self.datatype
            ),  # lista om metadata för flera paket från olika datatyper
            "monitoring_program": get_static_metadata(
                "monitoring_program", [self.monitoring_program], "en"
            ),  # lista om metadata skrivs för flera paket.
            "method_description": get_static_metadata(
                "methods",
                [self.monitoring_program, self.datatype.lower()],
                "en",
            ),
            "dataset_filename": self._source,  # lista om metadata skrivs för flera paket.
            "keywords": get_static_metadata(
                "keywords",
                [self.monitoring_program, self.datatype.lower(), "gcmd"],
                "en",
            ),
            "measuring_area_type": get_static_metadata(
                "misc",
                ["measuring_area_type", self.datatype.lower()],
                "en",
            ),  # point, polygon, transect, annat namn?
            "coordinate_system": get_static_metadata(
                "misc",
                ["coordinate_system", self.datatype.lower()],
                "en",
            ),  # alltid wgs84
            "platform_class": get_static_metadata(
                "misc", ["platform_class", self.datatype.lower()], "en"
            ),
            "license": get_static_metadata(
                "misc", ["license", self.datatype.lower()], "en"
            ),  # license.yaml, flyttat till misc
            "min_year": _apply_on_column(min, "visit_year", self._data),
            "max_year": _apply_on_column(max, "visit_year", self._data),
            "min_date": _apply_on_column(min, "sample_date", self._data),
            "max_date": _apply_on_column(max, "sample_date", self._data),
            "min_longitude_dd": _apply_on_column(min, "sample_longitude_dd", self._data),
            "max_longitude_dd": _apply_on_column(max, "sample_longitude_dd", self._data),
            "min_latitude_dd": _apply_on_column(min, "sample_latitude_dd", self._data),
            "max_latitude_dd": _apply_on_column(max, "sample_latitude_dd", self._data),
            "stations": _apply_on_column(
                lambda s: s.unique().to_list(), "station_name", self._data
            ),
            "parameters": _apply_on_column(
                lambda s: s.unique().to_list(), "parameter", self._data
            ),
            "taxonomic_coverage": _apply_on_column(
                lambda s: s.unique().to_list(), "scientific_name", self._data
            ),
            "originator": {
                "name": get_translate_codes_object().get_english_name(
                    "LABO", self.originator
                ),
                "contact": get_static_metadata(
                    "originator_contact",
                    [self.originator, self.datatype],
                    "en",
                ),
            },  # lista med flera dicts om flera datapaket läses.
            "orderer": get_translate_codes_object().get_english_name(
                "LABO", self.delivery_note.get("ORDERER", "sample_orderer_code")
            ),
            "data_holding_centre": {
                "name": get_static_metadata(
                    "misc",
                    ["data_holding_centre", self.datatype.lower(), "name"],
                ),
                "address": get_static_metadata(
                    "misc",
                    ["data_holding_centre", self.datatype.lower(), "address"],
                ),
                "postal_code": get_static_metadata(
                    "misc",
                    ["data_holding_centre", self.datatype.lower(), "postal_code"],
                ),
                "city": get_static_metadata(
                    "misc",
                    ["data_holding_centre", self.datatype.lower(), "city"],
                ),
                "phone": get_static_metadata(
                    "misc",
                    ["data_holding_centre", self.datatype.lower(), "phone"],
                ),
                "email": get_static_metadata(
                    "misc",
                    ["data_holding_centre", self.datatype.lower(), "email"],
                ),
            },
            "database_reference": get_static_metadata(
                "misc",
                ["database_reference", self.datatype.lower()],
            ),
            "internet_access": get_static_metadata(
                "url_linkage",
                ["shark", self.monitoring_program, self.datatype.lower()],
            )[0]["url"],  # url linkage,  shark.smhi.se, shark.smhi.se/api/docs
            "citation": get_static_metadata(
                "misc",
                ["citation", self.datatype.lower()],
            ).format(originator=self.originator, project=self.monitoring_program),
        }

    @classmethod
    def from_shark_package(cls, package_path: Path) -> Self:
        sharkadm_dataholder = get_polars_data_holder(package_path)
        return cls(
            data=sharkadm_dataholder.data,
            delivery_note=sharkadm_dataholder.delivery_note.data,
            source=package_path.name,
        )
