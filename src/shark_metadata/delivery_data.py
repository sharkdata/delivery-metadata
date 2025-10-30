from collections import defaultdict
from functools import cache
from importlib import resources
from pathlib import Path
from typing import Callable, Self

import polars as pl
import yaml
from nodc_codes import get_translate_codes_object
from sharkadm import controller as sharkadm_controller
from sharkadm import multi_transformers, transformers
from sharkadm.sharkadm_logger import adm_logger


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


def restructure_by_language(filename: str) -> dict:
    """
    Restructure the nested metadata dict so that 'en' and 'sv' become the top-level keys.

    Example:
        Input:
            {'NATL': {'bacterioplankton': {'en': 'text', 'sv': 'text'}}}
        Output:
            {'en': {'NATL': {'bacterioplankton': 'text'}},
             'sv': {'NATL': {'bacterioplankton': 'text'}}}
    """
    data = _load_yaml(filename)
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
    metadata = restructure_by_language(filename)
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
        return self.delivery_note.get("DTYPE") or self.delivery_note.get("DATA_FORMAT")

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

    def generate_readme(self):
        return get_static_metadata(
            "readme",
            ["default"],
            "en",
        )

    def generate_metadata(self):
        print("\n".join(sorted(self._data.columns)))
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
            "min_year": _apply_on_column(min, "visit_year", self.data),
            "max_year": _apply_on_column(max, "visit_year", self.data),
            "min_date": _apply_on_column(min, "sample_date", self.data),
            "max_date": _apply_on_column(max, "sample_date", self.data),
            "min_longitude_dd": _apply_on_column(min, "sample_longitude_dd", self.data),
            "max_longitude_dd": _apply_on_column(max, "sample_longitude_dd", self.data),
            "min_latitude_dd": _apply_on_column(min, "sample_latitude_dd", self.data),
            "max_latitude_dd": _apply_on_column(max, "sample_latitude_dd", self.data),
            # Which transformer to get station_name without synonyms, i.e. not reported_?
            "stations": _apply_on_column(
                lambda s: s.unique().to_list(), "reported_station_name", self.data
            ),
            "parameters": _apply_on_columns(
                build_parameter_unit_mapping, ["parameter", "unit"], self.data
            ),
            # Do we need a transformer to get the column scientific_name?
            # Do we want reported or a transformed column?
            "taxonomic_coverage": _apply_on_column(
                lambda s: s.unique().to_list(), "reported_scientific_name", self.data
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
                "LABO", self.delivery_note.get("sample_orderer_code", "Not specified")
            ),
            "data_holding_centre": get_static_metadata(
                "misc", ["data_holding_centre", "smhi"]
            ),
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
            ).format(
                originator=self.originator,
                project=get_translate_codes_object().get_english_name(
                    "project", self.monitoring_program
                ),
            ),
        }

    @classmethod
    def from_shark_package(cls, package_path: Path) -> Self:
        adm_logger.print_on_screen()
        controller = sharkadm_controller.get_polars_controller_with_data(package_path)
        print(f"\t\t{controller.data_holder.data.columns=}")
        print(f"\t\t{controller.data_holder.data_structure=}")
        for transformer, args, kwargs in (
            (transformers.PolarsReplaceCommaWithDot, (), {}),
            (multi_transformers.DateTimePolars, (), {}),
            (multi_transformers.PositionPolars, (), {}),
            (transformers.PolarsWideToLong, (), {}),
            (transformers.PolarsRemoveColumns, ("COPY_VARIABLE.*",), {}),
            # (transformers.AddStationInfo, (), {}), # uses pandas
        ):
            controller.transform(transformer(*args, **kwargs))

        sharkadm_dataholder = controller.data_holder
        return cls(
            data=sharkadm_dataholder.data,
            delivery_note=sharkadm_dataholder.delivery_note.data,
            source=package_path.name,
        )
