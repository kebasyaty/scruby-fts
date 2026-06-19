<div align="center">
  <p align="center">
    <a href="https://github.com/kebasyaty/scruby-fts">
      <img
        height="80"
        alt="Logo"
        src="https://raw.githubusercontent.com/kebasyaty/scruby-fts/v2/assets/logo.svg">
    </a>
  </p>
  <p>
    <h1>Scruby-FTS</h1>
    <h3>Plugin for Scruby - Full-text search with Manticore Search.</h3>
    <p align="center">
      <!-- <a href="https://github.com/kebasyaty/scruby-fts/actions/workflows/test.yml" alt="Build Status"><img src="https://github.com/kebasyaty/scruby-fts/actions/workflows/test.yml/badge.svg" alt="Build Status"></a> -->
      <a href="https://kebasyaty.github.io/scruby-fts/" alt="Docs"><img src="https://img.shields.io/badge/docs-available-brightgreen.svg" alt="Docs"></a>
      <a href="https://pypi.python.org/pypi/scruby-fts/" alt="PyPI pyversions"><img src="https://img.shields.io/pypi/pyversions/scruby-fts.svg" alt="PyPI pyversions"></a>
      <a href="https://pypi.python.org/pypi/scruby-fts/" alt="PyPI status"><img src="https://img.shields.io/pypi/status/scruby-fts.svg" alt="PyPI status"></a>
      <a href="https://pypi.python.org/pypi/scruby-fts/" alt="PyPI version fury.io"><img src="https://badge.fury.io/py/scruby-fts.svg" alt="PyPI version fury.io"></a>
      <br>
      <a href="https://pyrefly.org/" alt="Types: Pyrefly"><img src="https://img.shields.io/badge/types-Pyrefly-FFB74D.svg" alt="Types: Pyrefly"></a>
      <a href="https://docs.astral.sh/ruff/" alt="Code style: Ruff"><img src="https://img.shields.io/badge/code%20style-Ruff-FDD835.svg" alt="Code style: Ruff"></a>
      <a href="https://pypi.org/project/scruby-fts"><img src="https://img.shields.io/pypi/format/scruby-fts" alt="Format"></a>
      <a href="https://pepy.tech/projects/scruby-fts"><img src="https://static.pepy.tech/badge/scruby-fts" alt="PyPI Downloads"></a>
      <a href="https://github.com/kebasyaty/scruby-fts/blob/main/MIT-LICENSE" alt="License: MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
      <a href="https://github.com/kebasyaty/scruby-fts/blob/main/GPL-3.0-LICENSE" alt="License: GPL v3"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="License: GPL v3"></a>
    </p>
    <p align="center">
      Scruby-FTS is a plugin for the <a href="https://pypi.org/project/scruby/" alt="Scruby">Scruby</a> project.
    </p>
  </p>
</div>

##

<br>

[![Documentation](https://raw.githubusercontent.com/kebasyaty/scruby-fts/v2/assets/links/documentation.svg "Documentation")](https://kebasyaty.github.io/scruby-fts/ "Documentation")

[![Requirements](https://raw.githubusercontent.com/kebasyaty/scruby-fts/v2/assets/links/requirements.svg "Requirements")](https://github.com/kebasyaty/scruby-fts/blob/v2/REQUIREMENTS.md "Requirements")

## Installation

```shell
# For Scruby version 0
uv add "scruby-fts>=0.10.0,<1.0.0"
# For Scruby version 1
uv add "scruby-fts>=1.0.0,<2.0.0"
# For Scruby version 2
uv add "scruby-fts>=2.0.0,<3.0.0"
```

## Install Manticore Search

For more information, see the <a href="https://manticoresearch.com/install/" alt="Install">documentation</a>.

- **Fedora 42 or later**

```shell
# Install the repository:
sudo tee /etc/yum.repos.d/manticore.repo << "EOF" > /dev/null
[manticore]
name=Manticore Repository
baseurl=https://repo.manticoresearch.com/repository/manticoresearch/release/centos/10/$basearch
gpgcheck=1
enabled=1
gpgkey=https://repo.manticoresearch.com/GPG-KEY-SHA256-manticore
EOF

# Install Manticore Search:
sudo dnf install manticore manticore-extra
# Install English, German, and Russian lemmatizers:
sudo dnf install manticore-language-packs

# Run Manticore Search:
sudo systemctl start manticore
sudo systemctl enable manticore
sudo systemctl status manticore --no-pager -l
```

## Usage

[![Examples](https://raw.githubusercontent.com/kebasyaty/scruby-fts/v2/assets/links/examples.svg "Examples")](https://kebasyaty.github.io/scruby-fts/latest/pages/usage/ "Examples")

```python
import anyio
from typing import Any
from pydantic import Field
from scruby import ReturnType, Scruby, ScrubyModel
from scruby_fts import FullTextSearch, FTSConfig


class Car(ScrubyModel):
    brand: str = Field(strict=True, frozen=True)
    model: str = Field(strict=True, frozen=True)
    year: int = Field(strict=True, frozen=True)
    power_reserve: int = Field(strict=True, frozen=True)
    description: str = Field(strict=True)
    # key is always at bottom
    key: str = Field(
        strict=True,
        frozen=True,
        default_factory=lambda data: f"{data['brand']}:{data['model']}",
    )


async def main() -> None:
    """Example."""
    # Activate database.
    Scruby.run(plugins=[FullTextSearch])

    # Delete unnecessary tables that remain due to errors
    await FullTextSearch.delete_orphaned_tables()

    # Get collection `Car`
    car_coll = Scruby(Car)
    # Create cars.
    for num in range(1, 10):
        car = Car(
            brand="Mazda",
            model=f"EZ-6 {num}",
            year=2025,
            power_reserve=600,
            description="Electric cars are the future of the global automotive industry.",
        )
        await car_coll.add_doc(car)

    # Find car
    car: Car | None = await car_coll.plugins.fullTextSearch.find_one(
        morphology=FTSConfig.morphology.get("English"),  # 'English' or 'en'
        full_text_filter=("model", "EZ-6 9"),
    )

    # Return car in JSON format
    car: str | None = await car_coll.plugins.fullTextSearch.find_one(
        morphology=FTSConfig.morphology.get("English"),  # 'English' or 'en'
        full_text_filter=("model", "EZ-6 9"),
        return_type=ReturnType.JSON,
    )

    # Return car in Dictionary format
    car: dict | None = await car_coll.plugins.fullTextSearch.find_one(
        morphology=FTSConfig.morphology.get("English"),  # 'English' or 'en'
        full_text_filter=("model", "EZ-6 9"),
        return_type=ReturnType.DICT,
    )

    # Fand cars
    cars: list[Car] | None = await car_coll.plugins.fullTextSearch.find_many(
        morphology=FTSConfig.morphology.get("en"),  # 'en' or 'English'
        full_text_filter=("description", "future of automotive"),
    )

    # Return cars in JSON format
    cars: str | None = await car_coll.plugins.fullTextSearch.find_many(
        morphology=FTSConfig.morphology.get("en"),  # 'en' or 'English'
        full_text_filter=("description", "future of automotive"),
        return_type=ReturnType.JSON,
    )

    # Return cars in Dictionary format
    cars: list[dict] | None = await car_coll.plugins.fullTextSearch.find_many(
        morphology=FTSConfig.morphology.get("en"),  # 'en' or 'English'
        full_text_filter=("description", "future of automotive"),
        return_type=ReturnType.DICT,
    )

    # Full database deletion.
    # Hint: The main purpose is tests.
    Scruby.napalm()


if __name__ == "__main__":
    anyio.run(main)
```

<br>

[![Changelog](https://raw.githubusercontent.com/kebasyaty/scruby-fts/v2/assets/links/changelog.svg "Changelog")](https://github.com/kebasyaty/scruby-fts/blob/v2/CHANGELOG.md "Changelog")

[![MIT](https://raw.githubusercontent.com/kebasyaty/scruby-fts/v2/assets/links/mit.svg "MIT")](https://github.com/kebasyaty/scruby-fts/blob/main/MIT-LICENSE "MIT")

[![GPL-3.0](https://raw.githubusercontent.com/kebasyaty/scruby-fts/v2/assets/links/gpl-3.0-or-later.svg "GPL-3.0")](https://github.com/kebasyaty/scruby-fts/blob/main/GPL-3.0-LICENSE "GPL-3.0")
