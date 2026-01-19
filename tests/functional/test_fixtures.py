"""Smoke tests for core esstd fixtures."""


def test_root_view_fixture(root_view):
    """Verify root_view fixture creates a DictView."""
    assert root_view is not None
    assert root_view.container.path == ("/",)


def test_ctx_fixture(ctx):
    """Verify ctx fixture bundles root_view and storage_context."""
    from everyterm.term import Context

    assert isinstance(ctx, Context)
    assert ctx.default_context.root_view is not None
    assert ctx.default_context.storage_context is not None


def test_root_view_basic_operations(root_view):
    """Verify basic operations on root_view work."""
    # Store some data
    root_view.store({"test_key": "test_value"})

    # Extract and verify
    data = root_view.extract()
    assert "test_key" in data
    assert data["test_key"] == "test_value"
