import json
from pathlib import Path

import click
import polars as pl

from shark_metadata.delivery_data import DeliveryData


@click.command()
@click.argument("package", type=click.Path(exists=True, path_type=Path))
def cli(package: Path | pl.DataFrame):
    delivery_data = DeliveryData.from_path(package)
    print(delivery_data.delivery_note)
    metadata = delivery_data.generate_metadata()
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    readme = delivery_data.generate_readme()  # noqa: F841
    if package.parent.is_dir():
        with open(package.parent / "shark_metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    cli()
