"""TryCatch -- error handling flow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import Flow


if TYPE_CHECKING:
    from everybase import Context, Executable

    from .var import Var


__all__ = [
    "TryCatch",
]


class TryCatch(Flow):
    """Try/catch/finally error handling.

    Children layout: [body, catch?, finally?]

    Optional error Var is written with str(exception) on catch.

    Example::

        err = Var("")
        TryCatch(
            risky_operation,
            catch=error_handler,
            finally_=cleanup,
            error=err,
        )
    """

    def __init__(
        self,
        body: Executable,
        catch: Executable | None = None,
        finally_: Executable | None = None,
        *,
        error: Var[str] | None = None,
    ) -> None:
        """Initialize try/catch/finally flow.

        Args:
            body: Main execution body.
            catch: Executed on exception (optional).
            finally_: Executed always after body/catch (optional).
            error: Var written with str(exception) on catch (optional).
        """
        children: list[Executable] = [body]
        self._has_catch = catch is not None
        self._has_finally = finally_ is not None
        if catch is not None:
            children.append(catch)
        if finally_ is not None:
            children.append(finally_)
        super().__init__(*children)
        self._error = error

    async def execute(self, ctx: Context) -> None:
        """Execute with try/catch/finally semantics."""
        body = self.children[0]
        catch_idx = 1 if self._has_catch else None
        finally_idx: int | None = None
        if self._has_finally:
            finally_idx = 2 if self._has_catch else 1

        caught: Exception | None = None
        try:
            await body.execute(ctx)
        except Exception as e:
            caught = e
            if catch_idx is not None:
                if self._error is not None:
                    self._error.set(str(e))
                await self.children[catch_idx].execute(ctx)
        finally:
            if finally_idx is not None:
                await self.children[finally_idx].execute(ctx)

        if caught is not None and not self._has_catch:
            raise caught
