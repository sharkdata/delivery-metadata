from functools import cache
from importlib import resources
from pathlib import Path
from typing import Callable

import polars as pl
import yaml
from nodc_codes import get_translate_codes_object

from shark_metadata import errors


def _apply_on_column(function: Callable, column: str, dataframe: pl.DataFrame):
    if column not in dataframe.columns:
        return None

    return function(dataframe[column])


def _apply_on_columns(function: Callable, columns: list, dataframe: pl.DataFrame):
    if not all(col in dataframe.columns for col in columns):
        return None
    return function(dataframe.select(columns))


def build_parameter_unit_mapping(sub_df: pl.DataFrame):
    result = (
        sub_df.group_by("parameter").agg(pl.col("unit").unique()).to_dict(as_series=False)
    )
    return {p: u for p, u in zip(result["parameter"], result["unit"])}


@cache
def _load_yaml(filename: str) -> dict:
    resource = Path(resources.files(__package__)) / "metadata_config" / f"{filename}.yaml"
    if Path(resource).exists():
        with open(resource, encoding="utf-8") as f:
            return yaml.safe_load(f)
    else:
        return {}


def get_static_metadata(
    filename: str,
    keys: list,
    language: str = "en",
    directory: str = "shark_metadata_config",
    fallback=False,
):
    data = _load_yaml(filename)
    for key in keys:
        if value := data.get(key):
            data = value
        elif fallback:
            data = data.get("default", {})
        else:
            return None

    if language in data:
        return data[language]
    elif fallback:
        return data.get("en") or "NA"
    return None


class DeliveryData:
    def __init__(
        self,
        data: pl.DataFrame | None = None,
    ):
        # TODO: Kolla att alla relevanta fält finns i data
        self._data = data if data is not None else pl.DataFrame()

    @property
    def data(self):
        return self._data

    def _unique_values(self, column: str):
        try:
            return self.data[column].unique().to_list()
        except pl.exceptions.ColumnNotFoundError as polars_error:
            raise errors.MissingMetadataError(
                f"Missing column '{column}'."
            ) from polars_error

    def _single_value(self, column: str):
        unique_values = self._unique_values(column)
        assert len(unique_values) == 1, (
            f"Expected a single value for column {column}, got: {unique_values}"
        )
        return unique_values[0]

    @property
    def datatype(self):
        return self._single_value("delivery_datatype").lower().replace(" and ", "")

    @property
    def project(self):
        return self._unique_values("sample_project_name_en")

    @property
    def monitoring_program_code(self):
        return self._single_value("monitoring_program_code")

    @property
    def version(self):
        return self._single_value("version")

    @property
    def originator(self):
        return self._unique_values("reporting_institute_name_en")

    @property
    def orderer(self):
        return self._unique_values("sample_orderer_name_en")

    @property
    def dataset_name(self):
        return self._unique_values("dataset_name")

    def generate_readme(self):
        return get_static_metadata("readme", ["default"], "en")

    def generate_metadata(self, fallback=True):
        return {
            "dataset_filename": self.dataset_name[
                0
            ],  # lista om metadata skrivs för flera paket.
            "version": self.version,
            "datatype": get_translate_codes_object().get_english_name(
                "delivery_datatype", self.datatype
            ),  # lista om metadata för flera paket från olika datatyper
            "monitoring_program": get_static_metadata(
                "monitoring_program",
                [self.monitoring_program_code],
                "en",
                fallback=fallback,
            ),  # lista om metadata skrivs för flera paket.
            "method_description": get_static_metadata(
                "methods",
                [self.monitoring_program_code, self.datatype],
                "en",
                fallback=fallback,
            ),
            "originator": {
                "name": get_translate_codes_object().get_english_name(
                    "LABO", self.originator[0]
                ),
                "contact": get_static_metadata(
                    "originator_contact",
                    [
                        get_translate_codes_object().get_internal_value(
                            "LABO", self.originator[0]
                        ),
                        self.datatype[0],
                    ],
                    "en",
                ),
            },  # lista med flera dicts om flera datapaket läses.
            "orderer": get_translate_codes_object().get_english_name(
                "LABO", self.orderer[0]
            ),
            "data_holding_centre": get_static_metadata(
                "misc",
                ["data_holding_centre", "smhi"],
                fallback=fallback,
            ),
            "database_reference": get_static_metadata(
                "misc",
                ["database_reference", self.datatype[0].lower()],
                fallback=fallback,
            ),
            "internet_access": get_static_metadata(
                "url_linkage",
                ["shark", self.project[0], self.datatype[0].lower()],
                fallback=fallback,
            )[0]["url"],  # url linkage,  shark.smhi.se, shark.smhi.se/api/docs
            "license": get_static_metadata(
                "misc",
                ["license", self.datatype[0].lower()],
                "en",
                fallback=fallback,
            ),  # license.yaml, flyttat till misc
            "citation": get_static_metadata(
                "misc",
                ["citation", self.datatype[0].lower()],
                fallback=fallback,
            ).format(
                originator=self.originator[0],
                project=get_translate_codes_object().get_english_name(
                    "project", self.project[0]
                ),
            ),
            "gcmd_science_keywords": get_static_metadata(
                "keywords",
                [self.monitoring_program_code, self.datatype[0].lower(), "gcmd"],
                "en",
                fallback=fallback,
            ),
            "measuring_area_type": get_static_metadata(
                "misc",
                ["measuring_area_type", self.datatype[0].lower()],
                "en",
                fallback=fallback,
            ),  # point, polygon, transect, annat namn?
            "coordinate_system": get_static_metadata(
                "misc",
                ["coordinate_system", self.datatype[0].lower()],
                "en",
                fallback=fallback,
            ),  # alltid wgs84
            "min_longitude_dd": _apply_on_column(min, "sample_longitude_dd", self.data),
            "max_longitude_dd": _apply_on_column(max, "sample_longitude_dd", self.data),
            "min_latitude_dd": _apply_on_column(min, "sample_latitude_dd", self.data),
            "max_latitude_dd": _apply_on_column(max, "sample_latitude_dd", self.data),
            "min_year": _apply_on_column(min, "visit_year", self.data),
            "max_year": _apply_on_column(max, "visit_year", self.data),
            "min_date": _apply_on_column(min, "sample_date", self.data),
            "max_date": _apply_on_column(max, "sample_date", self.data),
            "stations": _apply_on_column(
                lambda s: s.unique().to_list(), "station_name", self.data
            ),
            "platform_class": get_static_metadata(
                "misc",
                ["platform_class", self.datatype[0].lower()],
                "en",
                fallback=fallback,
            ),
            "parameters": _apply_on_columns(
                build_parameter_unit_mapping, ["parameter", "unit"], self.data
            ),
            # Do we need a transformer to get the column scientific_name?
            # Do we want reported or a transformed column?
            "taxonomic_coverage": _apply_on_column(
                lambda s: s.unique().to_list(), "scientific_name", self.data
            ),
        }
