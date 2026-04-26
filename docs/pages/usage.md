#### Example of using the plugin

```py title="main.py" linenums="1"
import anyio
from typing import Any
from pydantic import Field
from scruby import Scruby, ScrubyModel, ScrubyConfig
from scruby_fts import FullTextSearch, FTSConfig
from pprint import pprint as pp

# Plugins connection.
ScrubyConfig.plugins = [
    FullTextSearch,
]


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
    # Delete unnecessary tables that remain due to errors
    await FullTextSearch.delete_orphaned_tables()

    # Get collection `Car`
    car_coll = await Scruby.collection(Car)
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

    # Find one car
    car = await car_coll.plugins.fullTextSearch.find_one(
        morphology=FTSConfig.morphology.get("English"),  # 'English' or 'en'
        full_text_filter=("model", "EZ-6 9"),
        # filter_fn=lambda doc: doc.brand == "Mazda",
    )
    if car is not None:
      pp(car)
    else:
      print("Not Found")

    # Fand many cars
    car_list = await car_coll.plugins.fullTextSearch.find_many(
        morphology=FTSConfig.morphology.get("en"),  # 'en' or 'English'
        full_text_filter=("description", "future of automotive"),
        # filter_fn=lambda doc: doc.brand == "Mazda",
    )
    if car_list is not None:
      pp(car_list)
    else:
      print("Not Found")

    # Full database deletion.
    # Hint: The main purpose is tests.
    Scruby.napalm()


if __name__ == "__main__":
    anyio.run(main)
```
