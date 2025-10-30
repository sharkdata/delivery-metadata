import json
from pathlib import Path

import click

from shark_metadata.delivery_data import DeliveryData


@click.command()
@click.argument("package", type=click.Path(exists=True, path_type=Path))
def cli(package: Path):
    delivery_data = DeliveryData.from_shark_package(package)
    metadata = delivery_data.generate_metadata()
    readme = delivery_data.generate_readme()
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    if package.is_dir():
        with open(package / "shark_metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(readme)
        with open(package / "readme.txt", "w", encoding="utf-8") as f:
            f.write(readme)
    else:
        pass


if __name__ == "__main__":
    cli()
