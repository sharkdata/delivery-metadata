import json
from pathlib import Path

import click

from shark_metadata.delivery_data import DeliveryData


@click.command()
@click.argument("package", type=click.Path(exists=True, path_type=Path))
def cli(package: Path):
    delivery_data = DeliveryData.from_shark_package(package)
    metadata = delivery_data.generate_metadata()
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    cli()
