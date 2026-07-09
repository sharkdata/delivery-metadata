import json
from pathlib import Path

import click
import polars as pl

from shark_metadata.delivery_data import DeliveryData
from shark_metadata.delivery_package import DeliveryPackage


@click.command()
@click.argument("package", type=click.Path(exists=True, path_type=Path))
def cli(package: Path | pl.DataFrame):
    delivery_package = DeliveryPackage.from_zip(package)
    if package.parent.is_dir():
        metadata_from_dataframe(delivery_package.enriched_data, Path(package.parent))

def metadata_from_dataframe(df, path):
    DeliveryData(df).save(path)


if __name__ == "__main__":
    cli()
