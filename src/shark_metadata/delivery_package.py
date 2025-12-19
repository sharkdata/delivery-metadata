import zipfile
from pathlib import Path
from typing import Self

import pandas as pd
import polars as pl

from shark_metadata import errors


class DeliveryPackage:
    def __init__(
        self,
        data: pl.DataFrame,
        original_path: Path,
        raw_delivery_note: str,
        encoding: str = "cp1252",
    ):
        self._data = data
        self._encoding = encoding
        self._original_path = original_path
        self._delivery_note = self._read_delivery_note(raw_delivery_note)

    @property
    def data(self) -> pl.DataFrame:
        return self._data.with_columns(pl.lit(self.version).alias("version"))

    @property
    def enriched_data(self) -> pl.DataFrame:
        df = self.data.clone()
        print(self.delivery_note["övervakningsprogram"])
        if "monitoring_program_code" in df.columns:
            # Replace nulls with delivery_note value
            df = df.with_columns(
                [
                    pl.col("monitoring_program_code").fill_null(
                        pl.lit(
                            self.delivery_note["övervakningsprogram"].lower(),
                            dtype=pl.Utf8,
                        )
                    )
                ]
            )
        else:
            # Column doesn't exist → add it
            df = df.with_columns(
                [
                    pl.lit(
                        self.delivery_note["övervakningsprogram"].lower(), dtype=pl.Utf8
                    ).alias("monitoring_program_code")
                ]
            )
        return df

    @property
    def delivery_note(self) -> dict:
        return self._delivery_note

    @property
    def version(self) -> str:
        return self._original_path.stem.split("_")[-1]

    def _read_delivery_note(self, raw_delivery_note: str):
        data = {}
        key = None
        for line in raw_delivery_note.split("\n"):
            if not (line := line.strip()):
                continue
            if ":" not in line:
                # Belongs to previous row
                data[key] += f" {line}"
                continue
            key, value = [item.strip() for item in line.split(":", 1)]
            key = key.lstrip("- ")
            data[key] = value
            if key.upper() == "FORMAT":
                parts = [item.strip() for item in value.split(":")]
                data["data_format"] = parts[0]
        return data

    @classmethod
    def from_directory(cls, delivery_path: Path, encoding="cp1252") -> Self:
        shark_data_path = delivery_path / "processed_data" / "data.txt"
        if not shark_data_path.exists():
            raise errors.MissingFileError(
                f"Could not find 'data.txt' in {delivery_path}/processed_data"
            )

        data = pl.read_csv(
            shark_data_path,
            encoding=encoding,
            separator="\t",
            infer_schema=False,
        )

        delivery_note_path = delivery_path / "processed_data" / "delivery_note.txt"
        if not delivery_note_path.exists():
            raise errors.MissingFileError(
                "Could not find 'delivery_note.txt' in "
                f"{delivery_path.parent.relative_to(delivery_path.parent)}"
            )
        return cls(data, delivery_path, delivery_note_path.read_text(encoding=encoding))

    @classmethod
    def from_zip(cls, zip_path: Path, encoding="cp1252") -> Self:
        archive = zipfile.ZipFile(zip_path, "r")
        if "shark_data.txt" not in archive.namelist():
            raise errors.MissingFileError(
                f"Could not find 'shark_data.txt' in {zip_path.name}"
            )

        with archive.open("shark_data.txt") as f:
            pdf = pd.read_csv(f, sep="\t", encoding="cp1252")
        data = pl.from_pandas(pdf)

        if "processed_data/delivery_note.txt" not in archive.namelist():
            raise errors.MissingFileError(
                f"Could not find 'delivery_note.txt' in {zip_path.name}"
            )

        raw_delivery_note = (
            archive.open("processed_data/delivery_note.txt")
            .read()
            .decode(encoding=encoding)
        )
        return cls(
            data,
            zip_path,
            raw_delivery_note,
        )


if __name__ == "__main__":
    DP = DeliveryPackage.from_zip(
        Path("../Testdata/3. Zippar/SHARK_Phytoplankton_2023_SMHI_version_2025-03-09.zip")
    )
    print(DP.enriched_data["monitoring_program_code"].head())
