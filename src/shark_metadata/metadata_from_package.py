import json
from pathlib import Path
from zipfile import ZipFile

import click

from shark_metadata.delivery_data import DeliveryData


@click.command()
@click.argument("package", type=click.Path(exists=True, path_type=Path))
def cli(package: Path):
    delivery_data = DeliveryData.from_shark_package(package)
    metadata = delivery_data.generate_metadata()
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    if package.is_dir():
        with open(package / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    else:
        pass
        # detta verkar modifiera zip-paketet,
        # zip-paketet borde kanske inte röras utanför sharkadm?
        # with ZipFile(package, mode="a") as zf:
        #     json_bytes = json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8")
        #     zf.writestr("metadata.json", json_bytes)


if __name__ == "__main__":
    cli()
