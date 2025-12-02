"""Functional tests for basic shapes."""


def test_basic_shapes_fixture_available(basic_shapes):
    """Verify basic_shapes fixture provides expected shapes."""
    assert "Profile" in basic_shapes
    assert "User" in basic_shapes


# ============================================================================
# PRIMITIVE SLOT OPERATIONS
# ============================================================================


def test_primitive_set_and_get(basic_shapes, ctx):
    """Test setting and getting primitive values."""
    User = basic_shapes["User"]

    User.id.set("user123").execute(ctx)
    user_id = User.id.get().execute(ctx)

    assert user_id == "user123"


def test_primitive_multiple_types(basic_shapes, ctx):
    """Test multiple primitive types (str, int)."""
    Profile = basic_shapes["Profile"]

    # String
    Profile.name.set("Alice").execute(ctx)
    name = Profile.name.get().execute(ctx)
    assert name == "Alice"

    # Int
    Profile.age.set(30).execute(ctx)
    age = Profile.age.get().execute(ctx)
    assert age == 30


def test_primitive_update_value(basic_shapes, ctx):
    """Test updating primitive values."""
    User = basic_shapes["User"]

    User.id.set("user123").execute(ctx)
    assert User.id.get().execute(ctx) == "user123"

    User.id.set("user456").execute(ctx)
    assert User.id.get().execute(ctx) == "user456"


# ============================================================================
# NESTED SHAPE NAVIGATION
# ============================================================================


def test_nested_shape_navigation(basic_shapes, ctx):
    """Test navigating through nested shapes."""
    User = basic_shapes["User"]

    # Navigate: User.profile.name
    User.profile.name.set("Alice").execute(ctx)
    name = User.profile.name.get().execute(ctx)

    assert name == "Alice"


def test_nested_shape_multiple_fields(basic_shapes, ctx):
    """Test setting multiple fields in nested shape."""
    User = basic_shapes["User"]

    # Set multiple fields in nested profile
    User.profile.name.set("Alice").execute(ctx)
    User.profile.age.set(30).execute(ctx)

    # Retrieve
    name = User.profile.name.get().execute(ctx)
    age = User.profile.age.get().execute(ctx)

    assert name == "Alice"
    assert age == 30


# ============================================================================
# SHAPE STORE AND EXTRACT
# ============================================================================


def test_shape_store_dict(basic_shapes, ctx):
    """Test storing complete shape data as dict."""
    User = basic_shapes["User"]

    User.profile.store({"name": "Bob", "age": 25}).execute(ctx)

    name = User.profile.name.get().execute(ctx)
    age = User.profile.age.get().execute(ctx)

    assert name == "Bob"
    assert age == 25


def test_shape_extract_dict(basic_shapes, ctx):
    """Test extracting shape as dict."""
    User = basic_shapes["User"]

    # Set up data
    User.profile.name.set("Charlie").execute(ctx)
    User.profile.age.set(35).execute(ctx)

    # Extract
    profile_data = User.profile.extract().execute(ctx)

    assert profile_data == {"name": "Charlie", "age": 35}


def test_combined_primitives_and_shapes(basic_shapes, ctx):
    """Test combination of primitive slots and shape slots."""
    User = basic_shapes["User"]

    # Set primitive on User
    User.id.set("user789").execute(ctx)

    # Set nested shape
    User.profile.name.set("Diana").execute(ctx)
    User.profile.age.set(28).execute(ctx)

    # Verify both
    assert User.id.get().execute(ctx) == "user789"
    assert User.profile.name.get().execute(ctx) == "Diana"
    assert User.profile.age.get().execute(ctx) == 28
