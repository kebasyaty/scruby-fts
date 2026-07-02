#### Example of using the plugin

```py title="main.py" linenums="1"
import anyio
from typing import Annotated, Any
from pydantic import Field
from scruby import ReturnType, Scruby, ScrubyModel
from scruby_fts import FullTextSearch, FTSConfig
from pprint import pprint as pp


class Car(ScrubyModel):
    """Car model."""

    brand: str = Field(frozen=True)
    model: str = Field(frozen=True)
    year: int
    power_reserve: int
    description: str
    # key is always at bottom
    key: Annotated[
        str,
        Field(
            frozen=True,
            default_factory=lambda data: f"{data['brand']}:{data['model']}",
        ),
    ]


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

    # Find one car
    car = await car_coll.plugins.fullTextSearch.find_one(
        morphology=FTSConfig.morphology.get("English"),  # 'English' or 'en'
        full_text_filter=("model", "EZ-6 9"),
    )
    if car is not None:
      pp(car)
    else:
      print("Not Found")

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

    # Fand many cars
    car_list = await car_coll.plugins.fullTextSearch.find_many(
        morphology=FTSConfig.morphology.get("en"),  # 'en' or 'English'
        full_text_filter=("description", "future of automotive"),
    )
    if car_list is not None:
      pp(car_list)
    else:
      print("Not Found")

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
