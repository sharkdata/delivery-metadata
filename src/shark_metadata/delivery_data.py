import pathlib
from collections import defaultdict
from functools import cache
from importlib import resources
from pathlib import Path
from typing import Callable, Self

import polars as pl
import yaml
from nodc_codes import get_translate_codes_object


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
        path: str = "",
    ):
        self._data = pl.DataFrame() if data is None else data
        self.path = path
        self._delivery_note(path)

    def _delivery_note(
        self,
        path: str | pathlib.Path,
        encoding: str = "cp1252",
    ):
        if "processed_data" not in [p for p in path.parent.iterdir() if p.is_dir()]:
            delivery_path = path.parent / "processed_data" / "delivery_note.txt"

        if not delivery_path.is_file():
            msg = f"File is not a valid delivery_note text file: {delivery_path}"
            raise FileNotFoundError(msg)

        data = dict()
        with open(delivery_path, encoding=encoding) as fid:
            mapped_key = None
            for line in fid:
                if not line.strip():
                    continue
                if ":" not in line:
                    # Belongs to previous row
                    data[mapped_key] = f"{data[mapped_key]} {line.strip()}"
                    continue
                key, value = [item.strip() for item in line.split(":", 1)]
                key = key.lstrip("- ")
                data[key] = value
                if key.upper() == "FORMAT":
                    parts = [item.strip() for item in value.split(":")]
                    data["data_format"] = parts[0]

        self._delivery_note = data

    @property
    def data(self):
        return self._data

    @property
    def delivery_note(self):
        return self._delivery_note

    @property
    def version(self):
        print(str(self.path.parent))
        return str(self.path.parent).split("/")[-1].split("_")[-1]

    @property
    def datatype(self):
        return self.data["delivery_datatype"].unique().to_list()

    @property
    def project(self):
        return self.data["sample_project_name_en"].unique().to_list()

    @property
    def monitoring_program_code(self):
        return self.delivery_note.get("övervakningsprogram", "NA")

    @property
    def originator(self):
        return self.data["reporting_institute_name_en"].unique().to_list()

    @property
    def orderer(self):
        return self.data["sample_orderer_name_en"].unique().to_list()

    @property
    def dataset_name(self):
        return self.data["dataset_name"].unique().to_list()

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
        print(self.project)
        return {
            "dataset_filename": self.dataset_name[
                0
            ],  # lista om metadata skrivs för flera paket.
            "version": self.version,
            "datatype": get_translate_codes_object().get_english_name(
                "delivery_datatype", self.datatype[0]
            ),  # lista om metadata för flera paket från olika datatyper
            "monitoring_program": get_static_metadata(
                "monitoring_program", [self.monitoring_program_code], "en"
            ),  # lista om metadata skrivs för flera paket.
            "method_description": get_static_metadata(
                "methods",
                [self.monitoring_program_code, self.datatype[0].lower().replace(" ", "")],
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

    @classmethod
    def from_path(cls, package_path: Path) -> Self:
        data = pl.read_csv(
            package_path, encoding="cp1252", separator="\t", infer_schema_length=10000
        )
        return cls(
            data=data,
            path=package_path,
        )
