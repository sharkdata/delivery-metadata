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
    delivery_data = DeliveryData(delivery_package.enriched_data)
    readme = delivery_data.generate_readme()
    metadata = delivery_data.generate_metadata()
    if package.parent.is_dir():
        with open(package.parent / "shark_metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        with open(package.parent / "readme.txt", "w", encoding="utf-8") as f:
            f.write(readme)


if __name__ == "__main__":
    cli()
