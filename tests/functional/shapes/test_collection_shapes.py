"""Functional tests for collection shapes."""


def test_collection_shapes_fixture_available(collection_shapes):
    """Verify collection_shapes fixture provides expected shapes."""
    assert "Order" in collection_shapes
    assert "Market" in collection_shapes


# ============================================================================
# SEQUENCE SHAPE SLOT (orders)
# ============================================================================


def test_sequence_shape_append(collection_shapes, ctx):
    """Test appending shapes to sequence."""
    Market = collection_shapes["Market"]

    Market.orders.append(
        {
            "symbol": "AAPL",
            "quantity": 100,
            "price": 150.5,
        }
    ).execute(ctx)

    Market.orders.append(
        {
            "symbol": "GOOGL",
            "quantity": 50,
            "price": 2800.0,
        }
    ).execute(ctx)

    # Verify both orders
    order0 = Market.orders[0].extract().execute(ctx)
    order1 = Market.orders[1].extract().execute(ctx)

    assert order0["symbol"] == "AAPL"
    assert order1["symbol"] == "GOOGL"


def test_sequence_shape_field_navigation(collection_shapes, ctx):
    """Test navigating to fields within sequence shapes."""
    Market = collection_shapes["Market"]

    Market.orders.append(
        {
            "symbol": "AAPL",
            "quantity": 100,
            "price": 150.5,
        }
    ).execute(ctx)

    # Navigate: Market.orders[0].price
    price = Market.orders[0].price.get().execute(ctx)
    symbol = Market.orders[0].symbol.get().execute(ctx)
    quantity = Market.orders[0].quantity.get().execute(ctx)

    assert price == 150.5
    assert symbol == "AAPL"
    assert quantity == 100


def test_sequence_shape_update_field(collection_shapes, ctx):
    """Test updating fields in sequence shapes."""
    Market = collection_shapes["Market"]

    Market.orders.append(
        {
            "symbol": "AAPL",
            "quantity": 100,
            "price": 150.0,
        }
    ).execute(ctx)

    # Update price
    Market.orders[0].price.set(155.0).execute(ctx)

    updated_price = Market.orders[0].price.get().execute(ctx)
    assert updated_price == 155.0


def test_sequence_shape_extract_all(collection_shapes, ctx):
    """Test extracting all items from sequence."""
    Market = collection_shapes["Market"]

    Market.orders.append({"symbol": "AAPL", "quantity": 100, "price": 150.0}).execute(ctx)
    Market.orders.append({"symbol": "GOOGL", "quantity": 50, "price": 2800.0}).execute(ctx)

    all_orders = Market.orders.extract().execute(ctx)

    assert len(all_orders) == 2
    assert all_orders[0]["symbol"] == "AAPL"
    assert all_orders[1]["symbol"] == "GOOGL"


# ============================================================================
# MAPPING SHAPE SLOT (symbols)
# ============================================================================


def test_mapping_shape_store(collection_shapes, ctx):
    """Test storing shapes to mapping."""
    Market = collection_shapes["Market"]

    Market.symbols.store(
        {
            "AAPL": {
                "symbol": "AAPL",
                "quantity": 100,
                "price": 150.5,
            },
            "GOOGL": {
                "symbol": "GOOGL",
                "quantity": 50,
                "price": 2800.0,
            },
        }
    ).execute(ctx)

    # Verify both symbols
    aapl = Market.symbols["AAPL"].extract().execute(ctx)
    googl = Market.symbols["GOOGL"].extract().execute(ctx)

    assert aapl["symbol"] == "AAPL"
    assert googl["price"] == 2800.0


def test_mapping_shape_field_navigation(collection_shapes, ctx):
    """Test navigating to fields within mapping shapes."""
    Market = collection_shapes["Market"]

    Market.symbols.store(
        {
            "AAPL": {
                "symbol": "AAPL",
                "quantity": 1000,
                "price": 150.5,
            }
        }
    ).execute(ctx)

    # Navigate: Market.symbols["AAPL"].price
    price = Market.symbols["AAPL"].price.get().execute(ctx)
    quantity = Market.symbols["AAPL"].quantity.get().execute(ctx)

    assert price == 150.5
    assert quantity == 1000


def test_mapping_shape_update_field(collection_shapes, ctx):
    """Test updating fields in mapping shapes."""
    Market = collection_shapes["Market"]

    Market.symbols.store(
        {
            "AAPL": {
                "symbol": "AAPL",
                "quantity": 100,
                "price": 150.0,
            }
        }
    ).execute(ctx)

    # Update price and quantity
    Market.symbols["AAPL"].price.set(155.0).execute(ctx)
    Market.symbols["AAPL"].quantity.set(200).execute(ctx)

    updated_price = Market.symbols["AAPL"].price.get().execute(ctx)
    updated_quantity = Market.symbols["AAPL"].quantity.get().execute(ctx)

    assert updated_price == 155.0
    assert updated_quantity == 200


def test_mapping_shape_extract_all(collection_shapes, ctx):
    """Test extracting all items from mapping."""
    Market = collection_shapes["Market"]

    Market.symbols.store(
        {
            "AAPL": {"symbol": "AAPL", "quantity": 100, "price": 150.0},
            "GOOGL": {"symbol": "GOOGL", "quantity": 50, "price": 2800.0},
        }
    ).execute(ctx)

    all_symbols = Market.symbols.extract().execute(ctx)

    assert len(all_symbols) == 2
    assert all_symbols["AAPL"]["price"] == 150.0
    assert all_symbols["GOOGL"]["quantity"] == 50


# ============================================================================
# SIMPLE COLLECTIONS (prices, volumes)
# ============================================================================


def test_mapping_slot_primitives(collection_shapes, ctx):
    """Test DictSlot with primitive values."""
    Market = collection_shapes["Market"]

    Market.prices["AAPL"].set(150.5).execute(ctx)
    Market.prices["GOOGL"].set(2800.0).execute(ctx)

    aapl_price = Market.prices["AAPL"].get().execute(ctx)
    googl_price = Market.prices["GOOGL"].get().execute(ctx)

    assert aapl_price == 150.5
    assert googl_price == 2800.0


def test_sequence_slot_primitives(collection_shapes, ctx):
    """Test ListSlot with primitive values."""
    Market = collection_shapes["Market"]

    Market.volumes.append(1000).execute(ctx)
    Market.volumes.append(2000).execute(ctx)
    Market.volumes.append(3000).execute(ctx)

    volume0 = Market.volumes[0].get().execute(ctx)
    volume2 = Market.volumes[2].get().execute(ctx)

    assert volume0 == 1000
    assert volume2 == 3000


def test_sequence_slot_extract(collection_shapes, ctx):
    """Test extracting sequence of primitives."""
    Market = collection_shapes["Market"]

    Market.volumes.append(100).execute(ctx)
    Market.volumes.append(200).execute(ctx)
    Market.volumes.append(300).execute(ctx)

    all_volumes = Market.volumes.extract().execute(ctx)

    assert all_volumes == [100, 200, 300]
