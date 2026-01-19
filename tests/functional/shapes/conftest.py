"""Fixtures for shape layer testing."""

import pytest

from everybase.slot import (
    DictSlot,
    FloatSlot,
    IntSlot,
    ListSlot,
    ShapesDictSlot,
    ShapesListSlot,
    ShapeSlot,
    StrSlot,
)
from everyterm import Shape


# ============================================================================
# Basic Shape Fixtures
# ============================================================================


@pytest.fixture
def basic_shapes() -> dict[str, type[Shape]]:
    """Basic shape definitions for testing primitive and nested shapes.

    Returns dict with:
        - Profile: Simple shape with name (str) and age (int)
        - User: Shape with id and nested Profile shape

    Usage:
        def test_example(basic_shapes, ctx):
            User = basic_shapes["User"]
            User.id.set("user123").execute(ctx)
            assert User.id.get().execute(ctx) == "user123"
    """

    class Profile(Shape):
        """User profile with basic information."""

        name = StrSlot()
        age = IntSlot()

    class User(Shape):
        """User with ID and nested profile."""

        id = StrSlot()
        profile = ShapeSlot(Profile)

    return {"Profile": Profile, "User": User}


# ============================================================================
# Collection Shape Fixtures
# ============================================================================


@pytest.fixture
def collection_shapes() -> dict[str, type[Shape]]:
    """Shape definitions with collections for testing sequences and mappings.

    Returns dict with:
        - Order: Trading order with symbol, quantity, price
        - Market: Market data with sequences and mappings of orders

    Usage:
        def test_example(collection_shapes, ctx):
            Market = collection_shapes["Market"]
            Market.orders.append({"symbol": "AAPL", "quantity": 100}).execute(ctx)
    """

    class Order(Shape):
        """Trading order information."""

        symbol = StrSlot()
        quantity = IntSlot()
        price = FloatSlot()

    class Market(Shape):
        """Market data with order collections."""

        # Sequence of Order shapes
        orders = ShapesListSlot(Order)

        # Mapping of symbol → Order
        symbols = ShapesDictSlot(Order)

        # Simple collections for testing
        prices = DictSlot(float)
        volumes = ListSlot(int)

    return {"Order": Order, "Market": Market}


# ============================================================================
# Complex Shape Fixtures
# ============================================================================


@pytest.fixture
def nested_shapes() -> dict[str, type[Shape]]:
    """Complex nested shape definitions for advanced testing.

    Returns dict with:
        - Address: Physical address
        - Contact: Contact information with address
        - Company: Organization with multiple contacts

    Usage:
        def test_example(nested_shapes, ctx):
            Company = nested_shapes["Company"]
            Company.name.set("Acme Inc").execute(ctx)
    """

    class Address(Shape):
        """Physical address."""

        street = StrSlot()
        city = StrSlot()
        country = StrSlot()
        postal_code = StrSlot()

    class Contact(Shape):
        """Contact information."""

        name = StrSlot()
        email = StrSlot()
        phone = StrSlot()
        address = ShapeSlot(Address)

    class Company(Shape):
        """Company with multiple contacts."""

        name = StrSlot()
        contacts = ShapesListSlot(Contact)
        headquarters = ShapeSlot(Address)

    return {"Address": Address, "Contact": Contact, "Company": Company}
