"""Runtime - execution context for EveryFlow."""

from __future__ import annotations

from contextlib import contextmanager
from logging import getLogger
from typing import TYPE_CHECKING

import attrs
from pv.storage import (
    SnapshotProtocol,
    TransactionProtocol,
)

from every._abc import Context


if TYPE_CHECKING:
    from collections.abc import Iterator

    from pv.loc import key
    from pv.storage import (
        StorageContextType,
        StorageProtocol,
    )
    from pv.view import View


if TYPE_CHECKING:
    from pv.storage import StorageProtocol
    from term.shape import Shape

__all__ = [
    "StorageProvider",
]

logger = getLogger(__name__)


@attrs.frozen
class StorageProvider:
    """Protocol for Runtime with specific capabilities."""

    # ==============================
    # Storages
    # ==============================

    storages: tuple[StorageProtocol, ...]
    """Storages this class provides."""

    # ==============================
    # Term Context config
    # ==============================

    shape_config: dict[type[Shape] | None, tuple[type[View], key.Key, int]]
    """Configuration to construct specific Contexts per Shape.

    Passed as:
    {
        Users: (
            View: DictView,  # Data structure of the root view this Shape is executed over
            tuple: ("/", "sub-storage"),  # Location of the root view this Shape is executed over
            int: 1,  # Storage instance index this Shape is executed over
        ),
        ...
    }

    The default config is located at key None:
    {
        None: (
            DictView,
            ("/",),
            0,
        ),
        ...
    }
    """

    # ==============================
    # Utility methods
    # ==============================

    @contextmanager
    def context(self, read_only: bool = False) -> Iterator[Context]:
        """Constrcut Context structure for Term execution.

        To enable flexibility of Terms execution, multi-context approach has been choosen.
        It requires properly set arguments over several dimensions.

        1. Storages
        Each Shape can be associated with a distinct Storage.
        This is achieved through passing storage_context per Shape.
        The rest are executed over the default storage_context.

        2. Views
        Each Shape can ba associated with a distinct View.
        For example, FlowState is executed on an isolated subtree (/, __flow__).
        The rest are executed over the default root_view.

        3. Transaction vs Snapshot
        Use write or read-only storage.

        Note: Storage and View selection is tied to a Term during a single execution.
        One can execute the same Term on different contexts and have different results.

        These dimesnions, combined together, enable a super-flexible execution of Terms.
        """
        # Config
        context_root_view: View | None = None
        context_root_ctx: StorageContextType | None = None
        context_config: dict[type[Shape], tuple[View, StorageContextType]] = {}

        # Resources to clean up
        opened_transactions: list[TransactionProtocol] = []
        opened_snapshots: list[SnapshotProtocol] = []

        # Storage to ctx map
        storage_idx_2_ctx: dict[int, StorageContextType] = {}

        try:
            for shape_cls, (
                view_for_shape,
                loc_for_shape,
                storage_idx,
            ) in self.shape_config.items():
                storage_for_shape = self.storages[storage_idx]

                if storage_idx not in storage_idx_2_ctx:
                    if storage_for_shape.read_only or read_only:
                        ctx = storage_for_shape.begin_snapshot()
                        opened_snapshots.append(ctx)
                    else:
                        ctx = storage_for_shape.begin_transaction()
                        opened_transactions.append(ctx)
                    storage_idx_2_ctx[storage_idx] = ctx
                else:
                    ctx = storage_idx_2_ctx[storage_idx]

                view_inst = view_for_shape.open_at_site(loc_for_shape, ctx)

                if shape_cls is None:
                    context_root_view = view_inst
                    context_root_ctx = ctx
                else:
                    context_config[shape_cls] = (view_inst, ctx)

            if context_root_view is None or context_root_ctx is None:
                raise ValueError(
                    "Root context config is not provided. shape_config should have key None for root config."
                )

            yield Context.create(context_root_view, context_root_ctx, contexts=context_config)

        except Exception as e:
            logger.error(f"Error during context creation cleanup: {e}")

            # Abort transactions
            for tx in opened_transactions:
                try:
                    tx.abort()
                except Exception as e:
                    logger.error(f"Error during storage context cleanup: {e}")
                    pass

            # Close snapshots
            for snap in opened_snapshots:
                try:
                    snap.close()
                except Exception as e:
                    logger.error(f"Error during storage context cleanup: {e}")
                    pass
        else:
            # Commit transactions
            for tx in opened_transactions:
                try:
                    tx.commit()
                except Exception as e:
                    logger.error(f"Error during storage context committment: {e}")
                    raise e

            # Close snapshots
            for snap in opened_snapshots:
                try:
                    snap.close()
                except Exception as e:
                    logger.error(f"Error during storage context cleanup: {e}")
                    pass

    @contextmanager
    def ensure_context(
        self,
        storage: StorageProtocol,
        storage_context: StorageContextType | None = None,
        read_only: bool = False,
    ) -> Iterator[StorageContextType]:
        """Context manager that provides storage context (either uses passed one or creates a new).

        Args:
            storage: Storage instance
            storage_context: Storage context (None or passed)
            read_only: If True, creates snapshot context. If False, creates transaction context.

        Yields:
            Object with appropriate context

        Example:
            ```python
            # Transaction context
            with ensure_context(ctx, read_only=True) as ctx:
                # guaranteed ctx existance
                pass
            ```
        """
        if storage_context is not None:
            # Noop - use existing context (like original with_transaction)
            yield storage_context
        else:
            # Create new context and manage its lifecycle
            new_ctx = storage.begin_snapshot() if read_only else storage.begin_transaction()
            created_ctx = True

            try:
                yield new_ctx
            except Exception:
                # Cleanup only if we created the context
                if created_ctx:
                    try:
                        if isinstance(new_ctx, SnapshotProtocol):
                            new_ctx.close()
                        elif isinstance(new_ctx, TransactionProtocol):
                            new_ctx.abort()
                    except Exception as e:
                        logger.error(f"Error during storage context cleanup: {e}")
                        # Cleanup failed, but we still want to propagate the original exception
                        pass
                raise
            else:
                # Finalize only if we created the context
                if created_ctx:
                    if isinstance(new_ctx, SnapshotProtocol):
                        new_ctx.close()
                    elif isinstance(new_ctx, TransactionProtocol):
                        new_ctx.commit()
