"""Test a settings module."""

from __future__ import annotations

import manticoresearch
import pytest
from pydantic import Field
from scruby import ReturnType, Scruby, ScrubyModel

from scruby_fts import FTSConfig, FullTextSearch

pytestmark = pytest.mark.asyncio(loop_scope="module")

# Delete DB.
# Hint: If the previous test failed and the database remains.
Scruby.napalm()


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
        # Activate database.
        Scruby.run(plugins=[FullTextSearch])
        #
        # Get collection `Car`
        car_coll = Scruby(Car)
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
        # Activate database.
        Scruby.run(plugins=[FullTextSearch])
        #
        # Get collection `Car`
        car_coll = Scruby(Car)
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

    async def test_support_scruby_version(self) -> None:
        """Check Scruby version."""
        assert FullTextSearch.SCRUBY_VERSION == 2

    async def test_find_one(self) -> None:
        """Test a `find_one` method."""
        # Activate database.
        Scruby.run(plugins=[FullTextSearch])
        #
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

        # Find a car
        # ReturnType MODEL
        car: Car | None = await car_coll.plugins.fullTextSearch.find_one(
            morphology=FTSConfig.morphology.get("English"),
            full_text_filter=("brand", "SONY"),
        )
        assert car is None
        # ReturnType MODEL
        car_2: Car | None = await car_coll.plugins.fullTextSearch.find_one(
            morphology=FTSConfig.morphology.get("English"),
            full_text_filter=("model", "EZ-6 9"),
            filter_fn=lambda doc: doc.brand == "Mazda",
        )
        assert car_2 is not None
        assert car_2.model == "EZ-6 9"
        # ReturnType JSON
        car_json: str | None = await car_coll.plugins.fullTextSearch.find_one(
            morphology=FTSConfig.morphology.get("English"),
            full_text_filter=("model", "EZ-6 9"),
            return_type=ReturnType.JSON,
        )
        assert car_json is not None
        assert isinstance(car_json, str)
        # ReturnType DICT
        car_dict: dict | None = await car_coll.plugins.fullTextSearch.find_one(
            morphology=FTSConfig.morphology.get("English"),
            full_text_filter=("model", "EZ-6 9"),
            return_type=ReturnType.DICT,
        )
        assert car_dict is not None
        assert isinstance(car_dict, dict)
        #
        # Delete DB.
        Scruby.napalm()

    async def test_find_many(self) -> None:
        """Test a `find_many` method."""
        # Activate database.
        Scruby.run(plugins=[FullTextSearch])
        #
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
        # Find a cars
        # ReturnType MODEL
        car_list: list[Car] | None = await car_coll.plugins.fullTextSearch.find_many(
            morphology=FTSConfig.morphology.get("en"),
            full_text_filter=("description", "the future of all humanity"),
        )
        assert car_list is None
        # ReturnType MODEL
        car_list_2: list[Car] | None = await car_coll.plugins.fullTextSearch.find_many(
            morphology=FTSConfig.morphology.get("en"),
            full_text_filter=("description", "future of automotive"),
            filter_fn=lambda doc: doc.brand == "Mazda",
        )
        assert car_list_2 is not None
        assert len(car_list_2 or []) == 9
        # ReturnType JSON
        cars_json: str | None = await car_coll.plugins.fullTextSearch.find_many(
            morphology=FTSConfig.morphology.get("en"),
            full_text_filter=("description", "future of automotive"),
            filter_fn=lambda doc: doc.brand == "Mazda",
            return_type=ReturnType.JSON,
        )
        assert cars_json is not None
        assert isinstance(cars_json, str)
        # ReturnType DICT
        cars_list_dict: list[dict] | None = await car_coll.plugins.fullTextSearch.find_many(
            morphology=FTSConfig.morphology.get("en"),
            full_text_filter=("description", "future of automotive"),
            filter_fn=lambda doc: doc.brand == "Mazda",
            return_type=ReturnType.DICT,
        )
        assert cars_list_dict is not None
        assert isinstance(cars_list_dict, list)
        assert isinstance(cars_list_dict[0], dict)
        #
        # Delete DB.
        Scruby.napalm()
