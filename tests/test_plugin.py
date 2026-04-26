"""Test a settings module."""

from __future__ import annotations

import manticoresearch
import pytest
from pydantic import Field
from scruby import Scruby, ScrubyConfig, ScrubyModel

from scruby_fts import FTSConfig, FullTextSearch

pytestmark = pytest.mark.asyncio(loop_scope="module")


# Plugins connection.
ScrubyConfig.plugins = [
    FullTextSearch,
]


class Car(ScrubyModel):
    """Car model."""

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


async def test_delete_orphaned_tables() -> None:
    """Delete unnecessary tables that remain due to errors."""
    await FullTextSearch.delete_orphaned_tables()


class TestNegative:
    """Negative tests."""

    async def test_full_text_filter_field_name(self) -> None:
        """Invalid full_text_filter[0]->field name."""
        # Delete DB.
        Scruby.napalm()
        #
        # Get collection `Car`
        car_coll = await Scruby.collection(Car)
        # Create car.
        car = Car(
            brand="Mazda",
            model="EZ-6",
            year=2025,
            power_reserve=600,
            description="Electric cars are the future of the global automotive industry.",
        )
        # add to database
        await car_coll.add_doc(car)

        with pytest.raises(
            AttributeError,
            match=r"'Car' object has no attribute 'non_existent_field'",
        ):
            await car_coll.plugins.fullTextSearch.find_one(
                morphology=FTSConfig.morphology.get("English"),
                full_text_filter=("non_existent_field", "Some query string"),
            )

        with pytest.raises(
            AttributeError,
            match=r"'Car' object has no attribute 'non_existent_field'",
        ):
            await car_coll.plugins.fullTextSearch.find_many(
                morphology=FTSConfig.morphology.get("English"),
                full_text_filter=("non_existent_field", "Some query string"),
            )
        #
        # Delete DB.
        Scruby.napalm()

    @pytest.mark.xfail(
        raises=manticoresearch.exceptions.ConflictException,
        strict=True,
    )
    async def test_full_text_filter_field_type(self) -> None:
        """Invalid full_text_filter[0]->field type."""
        # Delete DB.
        Scruby.napalm()
        #
        # Get collection `Car`
        car_coll = await Scruby.collection(Car)
        # Create car.
        car = Car(
            brand="Mazda",
            model="EZ-6",
            year=2025,
            power_reserve=600,
            description="Electric cars are the future of the global automotive industry.",
        )
        # add to database
        await car_coll.add_doc(car)

        await car_coll.plugins.fullTextSearch.find_one(
            morphology=FTSConfig.morphology.get("English"),
            full_text_filter=("year", "Some query string"),
        )

        await car_coll.plugins.fullTextSearch.find_many(
            morphology=FTSConfig.morphology.get("English"),
            full_text_filter=("year", "Some query string"),
        )
        #
        # Delete DB.
        Scruby.napalm()


class TestPositive:
    """Positive tests."""

    async def test_find_one(self) -> None:
        """Test a `find_one` method."""
        # Delete DB.
        Scruby.napalm()
        #
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
        # Find a car
        car: Car | None = await car_coll.plugins.fullTextSearch.find_one(
            morphology=FTSConfig.morphology.get("English"),
            full_text_filter=("brand", "SONY"),
        )

        assert car is None

        car_2: Car | None = await car_coll.plugins.fullTextSearch.find_one(
            morphology=FTSConfig.morphology.get("English"),
            full_text_filter=("model", "EZ-6 9"),
            filter_fn=lambda doc: doc.brand == "Mazda",
        )

        assert car_2.model == "EZ-6 9"
        #
        # Delete DB.
        Scruby.napalm()

    async def test_find_many(self) -> None:
        """Test a `find_many` method."""
        # Delete DB.
        Scruby.napalm()
        #
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
        # Find a car
        car_list: list[Car] | None = await car_coll.plugins.fullTextSearch.find_many(
            morphology=FTSConfig.morphology.get("en"),
            full_text_filter=("description", "the future of all humanity"),
        )
        assert car_list is None

        car_list_2: list[Car] | None = await car_coll.plugins.fullTextSearch.find_many(
            morphology=FTSConfig.morphology.get("en"),
            full_text_filter=("description", "future of automotive"),
            filter_fn=lambda doc: doc.brand == "Mazda",
        )
        assert car_list_2 is not None
        assert len(car_list_2 or []) == 9
        #
        # Delete DB.
        Scruby.napalm()
