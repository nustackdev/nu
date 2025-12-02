"""Fixtures for esstd layer (views + shapes)."""

import pytest

from everyshape.shape import Context
from everyshape.storage import TransactionProtocol
from everyshape.view import View


# ============================================================================
# Root View Fixture
# ============================================================================


@pytest.fixture
def root_view(tx: TransactionProtocol) -> View:
    """Root DictView for esstd tests.

    Creates the root container at "/" with DictView, providing a mapping
    interface to the entire tree. All other views should navigate from this root.

    Dependency chain: codec → storage → tx → root_view
    """
    from esstd.collections import DictView

    return DictView.open_root(ctx=tx)


# ============================================================================
# Context Fixture
# ============================================================================


@pytest.fixture
def ctx(root_view: View, tx: TransactionProtocol) -> Context:
    """Context bundling root view and transaction.

    Used by shapes layer for executing operations and commands.

    Dependency chain: codec → storage → tx → root_view → ctx
    """
    return Context(root_view=root_view, storage_context=tx)
