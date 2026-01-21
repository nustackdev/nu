"""Dict ISlice support. [experimental]."""

# This module provides islice operations for dict/mapping refs:
# - MappingISliceRef: Reference to an islice of a mapping
# - ISliceExtractOp: Extract islice as dict
# - ISliceKeysOp: Get keys from islice
# - ISliceValuesOp: Get values from islice
# - ISliceItemsOp: Get items from islice
# """

# from __future__ import annotations

# from typing import TYPE_CHECKING, Any

# from everyshape.loc import path
# from everyterm.shape import Shape
# from everyterm.term import Context, Operation, RValue, literal
# from everyterm.term.refs import MappingValueRef
# from everyshape.typing import EMPTY, Empty, Value
# from pv.view  import Convertible

# from ..refs.refs import MappingRef, MappingShapeRef, ShapeRef


# if TYPE_CHECKING:
#     pass


# __all__ = [
#     "MappingISliceRef",
#     "MappingShapeISliceRef",
#     "ISliceExtractOp",
#     "ISliceKeysOp",
#     "ISliceValuesOp",
#     "ISliceItemsOp",
#     "ShapeISliceExtractOp",
#     "ShapeISliceKeysOp",
#     "ShapeISliceValuesOp",
#     "ShapeISliceItemsOp",
# ]


# # =============================================================================
# # ISlice Operations
# # =============================================================================


# class ISliceExtractOp[K: int | str, V: Value](Operation[dict[K, V] | Empty, Context]):
#     """Extract operation for mapping islices.

#     Example:
#         >>> data = State.users.islice(0, 5).extract().execute(ctx)
#     """

#     def __init__(self, ref: MappingISliceRef[K, V]) -> None:
#         self.ref = ref
#         self.children = ()

#     def execute(self, context: Context) -> dict[K, V] | Empty:
#         # Walk up to find root MappingRef
#         current = self.ref
#         islice_chain: list[MappingISliceRef] = []

#         while isinstance(current, MappingISliceRef):
#             islice_chain.append(current)
#             current = current.parent_ref

#         map_ref = current
#         view_path = map_ref.resolve(context)

#         try:
#             if not view_path:
#                 map_view = context.get_context_for_shape(map_ref.get_root_shape()).root_view
#             else:
#                 map_view = path.navigate_view(
#                     context.get_context_for_shape(map_ref.get_root_shape()).root_view,
#                     view_path,
#                 )

#             if not isinstance(map_view, Convertible):
#                 raise TypeError("View does not implement Convertible")

#             data = map_view.extract()

#             # Apply islices from outermost to innermost
#             for islice_ref in reversed(islice_chain):
#                 keys = list(data.keys())[islice_ref.islice_start : islice_ref.islice_stop]
#                 data = {k: data[k] for k in keys}

#             return data
#         except KeyError:
#             return EMPTY

#     def __repr__(self) -> str:
#         return f"ISliceExtractOp({self.ref!r})"


# class ISliceKeysOp[K: (int, str)](Operation[list[K], Context]):
#     """Get keys from mapping islice.

#     Example:
#         >>> keys = State.users.islice(0, 5).islice_keys().execute(ctx)
#     """

#     def __init__(self, ref: MappingISliceRef[K, Any]) -> None:
#         self.ref = ref
#         self.children = ()

#     def execute(self, context: Context) -> list[K]:
#         current = self.ref
#         islice_chain: list[MappingISliceRef] = []

#         while isinstance(current, MappingISliceRef):
#             islice_chain.append(current)
#             current = current.parent_ref

#         map_ref = current
#         view_path = map_ref.resolve(context)

#         if not view_path:
#             map_view = context.get_context_for_shape(map_ref.get_root_shape()).root_view
#         else:
#             map_view = path.navigate_view(
#                 context.get_context_for_shape(map_ref.get_root_shape()).root_view,
#                 view_path,
#             )

#         if not isinstance(map_view, Convertible):
#             raise TypeError("View does not implement Convertible")

#         data = map_view.extract()

#         for islice_ref in reversed(islice_chain):
#             keys = list(data.keys())[islice_ref.islice_start : islice_ref.islice_stop]
#             data = {k: data[k] for k in keys}

#         return list(data.keys())

#     def __repr__(self) -> str:
#         return f"ISliceKeysOp({self.ref!r})"


# class ISliceValuesOp[V: Value](Operation[list[V], Context]):
#     """Get values from mapping islice.

#     Example:
#         >>> values = State.users.islice(0, 5).islice_values().execute(ctx)
#     """

#     def __init__(self, ref: MappingISliceRef[Any, V]) -> None:
#         self.ref = ref
#         self.children = ()

#     def execute(self, context: Context) -> list[V]:
#         current = self.ref
#         islice_chain: list[MappingISliceRef] = []

#         while isinstance(current, MappingISliceRef):
#             islice_chain.append(current)
#             current = current.parent_ref

#         map_ref = current
#         view_path = map_ref.resolve(context)

#         if not view_path:
#             map_view = context.get_context_for_shape(map_ref.get_root_shape()).root_view
#         else:
#             map_view = path.navigate_view(
#                 context.get_context_for_shape(map_ref.get_root_shape()).root_view,
#                 view_path,
#             )

#         if not isinstance(map_view, Convertible):
#             raise TypeError("View does not implement Convertible")

#         data = map_view.extract()

#         for islice_ref in reversed(islice_chain):
#             keys = list(data.keys())[islice_ref.islice_start : islice_ref.islice_stop]
#             data = {k: data[k] for k in keys}

#         return list(data.values())

#     def __repr__(self) -> str:
#         return f"ISliceValuesOp({self.ref!r})"


# class ISliceItemsOp[K: int | str, V: Value](Operation[list[tuple[K, V]], Context]):
#     """Get items from mapping islice.

#     Example:
#         >>> items = State.users.islice(0, 5).islice_items().execute(ctx)
#     """

#     def __init__(self, ref: MappingISliceRef[K, V]) -> None:
#         self.ref = ref
#         self.children = ()

#     def execute(self, context: Context) -> list[tuple[K, V]]:
#         current = self.ref
#         islice_chain: list[MappingISliceRef] = []

#         while isinstance(current, MappingISliceRef):
#             islice_chain.append(current)
#             current = current.parent_ref

#         map_ref = current
#         view_path = map_ref.resolve(context)

#         if not view_path:
#             map_view = context.get_context_for_shape(map_ref.get_root_shape()).root_view
#         else:
#             map_view = path.navigate_view(
#                 context.get_context_for_shape(map_ref.get_root_shape()).root_view,
#                 view_path,
#             )

#         if not isinstance(map_view, Convertible):
#             raise TypeError("View does not implement Convertible")

#         data = map_view.extract()

#         for islice_ref in reversed(islice_chain):
#             keys = list(data.keys())[islice_ref.islice_start : islice_ref.islice_stop]
#             data = {k: data[k] for k in keys}

#         return list(data.items())

#     def __repr__(self) -> str:
#         return f"ISliceItemsOp({self.ref!r})"


# # =============================================================================
# # ISlice Reference
# # =============================================================================


# class MappingISliceRef[K: int | str, V: Value](MappingRef[K, V]):
#     """Reference to an islice of a mapping.

#     Represents a range of items in a mapping based on iteration order.

#     Example:
#         class State(Shape):
#             users: MappingRef[str, int] = DictSlot(int)

#         # Access islice
#         State.users.islice(0, 5).extract()       # First 5 items
#         State.users.islice(10, 20).islice_keys() # Keys 10-19
#     """

#     islice_start: int
#     islice_stop: int | None

#     def __init__(
#         self,
#         islice_start: int,
#         islice_stop: int | None,
#         value_type: type[V],
#         parent_ref: MappingRef[K, V],
#     ) -> None:
#         """Initialize islice reference.

#         Args:
#             islice_start: Start index in iteration order
#             islice_stop: Stop index (None for end)
#             value_type: Python type of values
#             parent_ref: Parent mapping reference
#         """
#         super().__init__(
#             address=(),
#             value_type=value_type,
#             view_type=parent_ref.view_type,
#             parent_ref=parent_ref,
#         )
#         self.islice_start = islice_start
#         self.islice_stop = islice_stop

#     def __getitem__(self, key: K | RValue[K, Context]) -> MappingValueRef[V]:
#         """Subscript to get item reference."""
#         return MappingValueRef(
#             address=literal(key),
#             value_type=self.value_type,
#             parent_ref=self,
#         )

#     def islice(self, start: int = 0, stop: int | None = None) -> MappingISliceRef[K, V]:
#         """Create nested islice."""
#         # Combine offsets
#         new_start = self.islice_start + start
#         new_stop = None
#         if stop is not None:
#             new_stop = self.islice_start + stop
#         if self.islice_stop is not None and (new_stop is None or new_stop > self.islice_stop):
#             new_stop = self.islice_stop
#         return MappingISliceRef(
#             islice_start=new_start,
#             islice_stop=new_stop,
#             value_type=self.value_type,
#             parent_ref=self.parent_ref,  # type: ignore[arg-type]
#         )

#     def extract(self) -> ISliceExtractOp[K, V]:  # type: ignore[override]
#         """Extract islice as dict."""
#         return ISliceExtractOp(self)

#     def islice_keys(self) -> ISliceKeysOp[K]:
#         """Get keys from islice."""
#         return ISliceKeysOp(self)

#     def islice_values(self) -> ISliceValuesOp[V]:
#         """Get values from islice."""
#         return ISliceValuesOp(self)

#     def islice_items(self) -> ISliceItemsOp[K, V]:
#         """Get items from islice."""
#         return ISliceItemsOp(self)

#     def resolve(self, context: Context) -> path.PathToView:
#         """Resolve to parent's path - islice is transparent."""
#         return self.parent_ref.resolve(context)  # type: ignore[union-attr]


# # =============================================================================
# # Shape ISlice Operations
# # =============================================================================


# class ShapeISliceExtractOp[K: int | str, T: Shape](Operation[dict[K, dict] | Empty, Context]):
#     """Extract operation for mapping shape islices.

#     Example:
#         >>> data = State.symbols.islice(0, 5).extract().execute(ctx)
#     """

#     def __init__(self, ref: MappingShapeISliceRef[K, T]) -> None:
#         self.ref = ref
#         self.children = ()

#     def execute(self, context: Context) -> dict[K, dict] | Empty:
#         # Walk up to find root MappingShapeRef
#         current = self.ref
#         islice_chain: list[MappingShapeISliceRef] = []

#         while isinstance(current, MappingShapeISliceRef):
#             islice_chain.append(current)
#             current = current.parent_ref

#         map_ref: MappingShapeRef = current  # type: ignore[assignment]
#         view_path = map_ref.resolve(context)

#         try:
#             if not view_path:
#                 map_view = context.get_context_for_shape(map_ref.get_root_shape()).root_view
#             else:
#                 map_view = path.navigate_view(
#                     context.get_context_for_shape(map_ref.get_root_shape()).root_view,
#                     view_path,
#                 )

#             if not isinstance(map_view, Convertible):
#                 raise TypeError("View does not implement Convertible")

#             data = map_view.extract()

#             # Apply islices from outermost to innermost
#             for islice_ref in reversed(islice_chain):
#                 keys = list(data.keys())[islice_ref.islice_start : islice_ref.islice_stop]
#                 data = {k: data[k] for k in keys}

#             return data
#         except KeyError:
#             return EMPTY

#     def __repr__(self) -> str:
#         return f"ShapeISliceExtractOp({self.ref!r})"


# class ShapeISliceKeysOp[K: (int, str)](Operation[list[K], Context]):
#     """Get keys from mapping shape islice.

#     Example:
#         >>> keys = State.symbols.islice(0, 5).islice_keys().execute(ctx)
#     """

#     def __init__(self, ref: MappingShapeISliceRef[K, Any]) -> None:
#         self.ref = ref
#         self.children = ()

#     def execute(self, context: Context) -> list[K]:
#         current = self.ref
#         islice_chain: list[MappingShapeISliceRef] = []

#         while isinstance(current, MappingShapeISliceRef):
#             islice_chain.append(current)
#             current = current.parent_ref

#         map_ref: MappingShapeRef = current  # type: ignore[assignment]
#         view_path = map_ref.resolve(context)

#         if not view_path:
#             map_view = context.get_context_for_shape(map_ref.get_root_shape()).root_view
#         else:
#             map_view = path.navigate_view(
#                 context.get_context_for_shape(map_ref.get_root_shape()).root_view,
#                 view_path,
#             )

#         if not isinstance(map_view, Convertible):
#             raise TypeError("View does not implement Convertible")

#         data = map_view.extract()

#         for islice_ref in reversed(islice_chain):
#             keys = list(data.keys())[islice_ref.islice_start : islice_ref.islice_stop]
#             data = {k: data[k] for k in keys}

#         return list(data.keys())

#     def __repr__(self) -> str:
#         return f"ShapeISliceKeysOp({self.ref!r})"


# class ShapeISliceValuesOp[T: Shape](Operation[list[dict], Context]):
#     """Get values from mapping shape islice.

#     Example:
#         >>> values = State.symbols.islice(0, 5).islice_values().execute(ctx)
#     """

#     def __init__(self, ref: MappingShapeISliceRef[Any, T]) -> None:
#         self.ref = ref
#         self.children = ()

#     def execute(self, context: Context) -> list[dict]:
#         current = self.ref
#         islice_chain: list[MappingShapeISliceRef] = []

#         while isinstance(current, MappingShapeISliceRef):
#             islice_chain.append(current)
#             current = current.parent_ref

#         map_ref: MappingShapeRef = current  # type: ignore[assignment]
#         view_path = map_ref.resolve(context)

#         if not view_path:
#             map_view = context.get_context_for_shape(map_ref.get_root_shape()).root_view
#         else:
#             map_view = path.navigate_view(
#                 context.get_context_for_shape(map_ref.get_root_shape()).root_view,
#                 view_path,
#             )

#         if not isinstance(map_view, Convertible):
#             raise TypeError("View does not implement Convertible")

#         data = map_view.extract()

#         for islice_ref in reversed(islice_chain):
#             keys = list(data.keys())[islice_ref.islice_start : islice_ref.islice_stop]
#             data = {k: data[k] for k in keys}

#         return list(data.values())

#     def __repr__(self) -> str:
#         return f"ShapeISliceValuesOp({self.ref!r})"


# class ShapeISliceItemsOp[K: int | str, T: Shape](Operation[list[tuple[K, dict]], Context]):
#     """Get items from mapping shape islice.

#     Example:
#         >>> items = State.symbols.islice(0, 5).islice_items().execute(ctx)
#     """

#     def __init__(self, ref: MappingShapeISliceRef[K, T]) -> None:
#         self.ref = ref
#         self.children = ()

#     def execute(self, context: Context) -> list[tuple[K, dict]]:
#         current = self.ref
#         islice_chain: list[MappingShapeISliceRef] = []

#         while isinstance(current, MappingShapeISliceRef):
#             islice_chain.append(current)
#             current = current.parent_ref

#         map_ref: MappingShapeRef = current  # type: ignore[assignment]
#         view_path = map_ref.resolve(context)

#         if not view_path:
#             map_view = context.get_context_for_shape(map_ref.get_root_shape()).root_view
#         else:
#             map_view = path.navigate_view(
#                 context.get_context_for_shape(map_ref.get_root_shape()).root_view,
#                 view_path,
#             )

#         if not isinstance(map_view, Convertible):
#             raise TypeError("View does not implement Convertible")

#         data = map_view.extract()

#         for islice_ref in reversed(islice_chain):
#             keys = list(data.keys())[islice_ref.islice_start : islice_ref.islice_stop]
#             data = {k: data[k] for k in keys}

#         return list(data.items())

#     def __repr__(self) -> str:
#         return f"ShapeISliceItemsOp({self.ref!r})"


# # =============================================================================
# # Shape ISlice Reference
# # =============================================================================


# class MappingShapeISliceRef[K: int | str, T: Shape](MappingShapeRef[K, T]):
#     """Reference to an islice of a mapping of shapes.

#     Represents a range of shapes in a mapping based on iteration order.

#     Example:
#         class State(Shape):
#             symbols: MappingShapeRef[str, SymbolInfo] = ShapesDictSlot(SymbolInfo)

#         # Access islice
#         State.symbols.islice(0, 5).extract()       # First 5 items
#         State.symbols.islice(10, 20).islice_keys() # Keys 10-19
#     """

#     islice_start: int
#     islice_stop: int | None

#     def __init__(
#         self,
#         islice_start: int,
#         islice_stop: int | None,
#         shape_type: type[T],
#         parent_ref: MappingShapeRef[K, T],
#     ) -> None:
#         """Initialize islice reference.

#         Args:
#             islice_start: Start index in iteration order
#             islice_stop: Stop index (None for end)
#             shape_type: Shape type of values
#             parent_ref: Parent mapping reference
#         """
#         super().__init__(
#             address=(),
#             shape_type=shape_type,
#             view_type=parent_ref.view_type,
#             parent_ref=parent_ref,
#             owner_shape=parent_ref.owner_shape,
#         )
#         self.islice_start = islice_start
#         self.islice_stop = islice_stop

#     def __getitem__(self, key: K | RValue[K, Context]) -> ShapeRef[T]:
#         """Subscript to get shape reference."""
#         from everybase.shape import DictView

#         from ..view_refs import ShapeRef

#         return ShapeRef(
#             address=literal(key),
#             shape_type=self.shape_type,
#             view_type=DictView,
#             parent_ref=self,
#         )  # type: ignore[return-value]

#     def islice(self, start: int = 0, stop: int | None = None) -> MappingShapeISliceRef[K, T]:
#         """Create nested islice."""
#         # Combine offsets
#         new_start = self.islice_start + start
#         new_stop = None
#         if stop is not None:
#             new_stop = self.islice_start + stop
#         if self.islice_stop is not None and (new_stop is None or new_stop > self.islice_stop):
#             new_stop = self.islice_stop
#         return MappingShapeISliceRef(
#             islice_start=new_start,
#             islice_stop=new_stop,
#             shape_type=self.shape_type,
#             parent_ref=self.parent_ref,  # type: ignore[arg-type]
#         )

#     def extract(self) -> ShapeISliceExtractOp[K, T]:  # type: ignore[override]
#         """Extract islice as dict."""
#         return ShapeISliceExtractOp(self)

#     def islice_keys(self) -> ShapeISliceKeysOp[K]:
#         """Get keys from islice."""
#         return ShapeISliceKeysOp(self)

#     def islice_values(self) -> ShapeISliceValuesOp[T]:
#         """Get values from islice."""
#         return ShapeISliceValuesOp(self)

#     def islice_items(self) -> ShapeISliceItemsOp[K, T]:
#         """Get items from islice."""
#         return ShapeISliceItemsOp(self)

#     def resolve(self, context: Context) -> path.PathToView:
#         """Resolve to parent's path - islice is transparent."""
#         return self.parent_ref.resolve(context)  # type: ignore[union-attr]
