from collections import defaultdict
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


def restructure_by_language(data: dict) -> dict:
    """
    Restructure the nested metadata dict so that 'en' and 'sv' become the top-level keys.

    Example:
        Input:
            {'NATL': {'bacterioplankton': {'en': 'text', 'sv': 'text'}}}
        Output:
            {'en': {'NATL': {'bacterioplankton': 'text'}},
             'sv': {'NATL': {'bacterioplankton': 'text'}}}
    """
    result = defaultdict(lambda: defaultdict(dict))

    def walk(node, path):
        if isinstance(node, dict):
            langs = {"en", "sv"} & node.keys()  # find intersection
            if langs:
                for lang in langs:
                    # navigate to the correct nested location in result[lang]
                    d = result[lang]
                    for key in path[:-1]:
                        d = d.setdefault(key, {})
                    d[path[-1]] = node[lang]
            else:
                for k, v in node.items():
                    walk(v, [*path, k])

    walk(data, [])

    return {lang: dict(result[lang]) for lang in result}


def get_static_metadata(filename: str, keys: list, lang: str = "en"):
    data = _load_yaml(filename)
    metadata = restructure_by_language(data)
    if metadata.get(lang):
        metadata = metadata.get(lang)
        for key in keys:
            metadata = metadata.get(key) or metadata.get("default")
            if metadata is None:
                return "NA"
    return metadata


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
        # return self.delivery_note.get("övervakningsprogram", "NA")

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

    @property
    def fields(self):
        return self._fields

    def generate_readme(self):
        return get_static_metadata("readme", ["default"], "en")

    def generate_metadata(self):
        return {
            "dataset_filename": self.dataset_name[
                0
            ],  # lista om metadata skrivs för flera paket.
            "version": self.version,
            "datatype": get_translate_codes_object().get_english_name(
                "delivery_datatype", self.datatype
            ),  # lista om metadata för flera paket från olika datatyper
            "monitoring_program": get_static_metadata(
                "monitoring_program", [self.monitoring_program_code], "en"
            ),  # lista om metadata skrivs för flera paket.
            "method_description": get_static_metadata(
                "methods",
                [self.monitoring_program_code, self.datatype],
                "en",
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
                "misc", ["data_holding_centre", "smhi"]
            ),
            "database_reference": get_static_metadata(
                "misc",
                ["database_reference", self.datatype[0].lower()],
            ),
            "internet_access": get_static_metadata(
                "url_linkage",
                ["shark", self.project[0], self.datatype[0].lower()],
            )[0]["url"],  # url linkage,  shark.smhi.se, shark.smhi.se/api/docs
            "license": get_static_metadata(
                "misc", ["license", self.datatype[0].lower()], "en"
            ),  # license.yaml, flyttat till misc
            "citation": get_static_metadata(
                "misc",
                ["citation", self.datatype[0].lower()],
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
            ),
            "measuring_area_type": get_static_metadata(
                "misc",
                ["measuring_area_type", self.datatype[0].lower()],
                "en",
            ),  # point, polygon, transect, annat namn?
            "coordinate_system": get_static_metadata(
                "misc",
                ["coordinate_system", self.datatype[0].lower()],
                "en",
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
                "misc", ["platform_class", self.datatype[0].lower()], "en"
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
