# """Slices. [experimental]"""

# from __future__ import annotations

# from typing import TYPE_CHECKING, overload

# from everyshape.loc import path
# from everyterm.term import Context, Operation, RValue, ViewRef, literal
# from everyterm.term.refs import SequenceValueRef
# from everyshape.typing import EMPTY, Empty, Sentinel, Value
# from pv.view  import (
#     Convertible,
#     Sizeable,
# )

# from ..refs.refs import SequenceRef, SequenceShapeRef, ShapeRef


# if TYPE_CHECKING:
#     from everyterm.shape import Shape


# class SliceExtractOp[T: Value](Operation[list[T] | Empty]):
#     """Extract operation for sequence slices.

#     Pure operation that reads a slice of a sequence and returns
#     it as a list.

#     Example:
#         >>> prices = Market.prices[1:5].extract().execute(ctx)
#         >>> # Returns: [10.5, 11.2, 12.0, 9.8]
#     """

#     def __init__(self, ref: SequenceSliceRef[T]) -> None:
#         """Initialize slice extract operation.

#         Args:
#             ref: Slice reference to extract from
#         """
#         self.ref = ref
#         self.children = ()

#     def execute(self, context: Context) -> list[T] | Empty:
#         """Execute slice extract operation.

#         Navigates to sequence location and extracts the slice.

#         Args:
#             context: Execution context

#         Returns:
#             List with extracted slice data, or Empty if not found
#         """

#         # Walk up the parent chain to find the root SequenceRef
#         current = self.ref
#         slice_chain: list[SequenceSliceRef] = []

#         while isinstance(current, SequenceSliceRef):
#             slice_chain.append(current)
#             current = current.parent_ref

#         # current is now the SequenceRef
#         seq_ref = current

#         # Resolve ref to Path
#         view_path = seq_ref.resolve(context)

#         # Navigate to the sequence's view
#         try:
#             if not view_path:
#                 # Root shape
#                 seq_view = context.get_context_for_shape(seq_ref.get_root_shape()).root_view
#             else:
#                 seq_view = path.navigate_view(
#                     context.get_context_for_shape(seq_ref.get_root_shape()).root_view,
#                     view_path,
#                 )

#             # Extract the full sequence first
#             if not isinstance(seq_view, Convertible):
#                 raise TypeError(
#                     f"View {seq_view.__class__.__name__} does not implement Convertible protocol."
#                 )

#             data = list(seq_view.extract())

#             # Apply slices from outermost to innermost
#             for slice_ref in reversed(slice_chain):
#                 slc = slice(slice_ref.slice_start, slice_ref.slice_stop, slice_ref.slice_step)
#                 data = data[slc]

#             return data
#         except KeyError:
#             return EMPTY

#     def __repr__(self) -> str:
#         return f"SliceExtractOp({self.ref!r})"


# class ShapeSliceExtractOp[T: Shape](Operation[list[dict] | Empty]):
#     """Extract operation for sequence shape slices.

#     Pure operation that reads a slice of a sequence of shapes and returns
#     it as a list of dicts.

#     Example:
#         >>> orders = Market.orders[1:5].extract().execute(ctx)
#         >>> # Returns: [{"id": "1", "price": 10.5}, {"id": "2", "price": 11.2}, ...]
#     """

#     def __init__(self, ref: SequenceShapeSliceRef[T]) -> None:
#         """Initialize shape slice extract operation.

#         Args:
#             ref: Shape slice reference to extract from
#         """
#         self.ref = ref
#         self.children = ()

#     def execute(self, context: Context) -> list[dict] | Empty:
#         """Execute shape slice extract operation.

#         Navigates to sequence location and extracts the slice.

#         Args:
#             context: Execution context

#         Returns:
#             List of dicts with extracted slice data, or Empty if not found
#         """

#         # Walk up the parent chain to find the root SequenceShapeRef
#         current = self.ref
#         slice_chain: list[SequenceShapeSliceRef] = []

#         while isinstance(current, SequenceShapeSliceRef):
#             slice_chain.append(current)
#             current = current.parent_ref

#         # current is now the SequenceShapeRef
#         seq_ref = current
#         if seq_ref is None:
#             raise

#         # Resolve ref to Path
#         view_path = seq_ref.resolve(context)

#         # Navigate to the sequence's view
#         try:
#             if not view_path:
#                 # Root shape
#                 seq_view = context.get_context_for_shape(seq_ref.get_root_shape()).root_view
#             else:
#                 seq_view = path.navigate_view(
#                     context.get_context_for_shape(seq_ref.get_root_shape()).root_view,
#                     view_path,
#                 )

#             # Extract the full sequence first
#             if not isinstance(seq_view, Convertible):
#                 raise TypeError(
#                     f"View {seq_view.__class__.__name__} does not implement Convertible protocol."
#                 )

#             data = seq_view.extract()

#             # Apply slices from outermost to innermost
#             for slice_ref in reversed(slice_chain):
#                 slc = slice(slice_ref.slice_start, slice_ref.slice_stop, slice_ref.slice_step)
#                 data = data[slc]

#             return data
#         except KeyError:
#             return EMPTY

#     def __repr__(self) -> str:
#         return f"ShapeSliceExtractOp({self.ref!r})"


# class SliceIndexOp(Operation[int]):
#     """Computes the actual index for a slice-relative index.

#     When accessing items from a slice (e.g., `seq[4:10][0]`), the index `0`
#     is relative to the slice. This operation computes the actual index in
#     the original sequence: `start + index * step`.

#     Handles negative indices by computing slice length at runtime.

#     Example:
#         >>> # For slice [4:10] with step 1, index 0 -> actual index 4
#         >>> op = SliceIndexOp(slice_start=4, slice_stop=10, slice_step=1, relative_index=0, parent_ref=ref)
#         >>> op.execute(ctx)  # Returns 4
#         >>> # For slice [4:10], index -1 -> actual index 9
#         >>> op = SliceIndexOp(slice_start=4, slice_stop=10, slice_step=1, relative_index=-1, parent_ref=ref)
#         >>> op.execute(ctx)  # Returns 9
#     """

#     def __init__(
#         self,
#         slice_start: int | None,
#         slice_stop: int | None,
#         slice_step: int | None,
#         relative_index: int | RValue[int],
#         parent_ref: ViewRef,
#     ) -> None:
#         """Initialize slice index operation.

#         Args:
#             slice_start: Start index of slice (None means 0)
#             slice_stop: Stop index of slice (None means end)
#             slice_step: Step of slice (None means 1)
#             relative_index: Index relative to the slice
#             parent_ref: Reference to parent sequence (for computing length)
#         """
#         self.slice_start = slice_start
#         self.slice_stop = slice_stop
#         self.slice_step = slice_step if slice_step is not None else 1
#         self.relative_index = relative_index
#         self.parent_ref = parent_ref
#         self.children = (literal(relative_index),) if isinstance(relative_index, RValue) else ()

#     def execute(self, context: Context) -> int:
#         """Compute the actual index.

#         Args:
#             context: Execution context

#         Returns:
#             The actual index in the original sequence
#         """
#         from everyshape.loc import path

#         if isinstance(self.relative_index, RValue):
#             rel_idx = self.relative_index.execute(context)
#         else:
#             rel_idx = self.relative_index

#         # Get the parent sequence length to properly compute slice bounds
#         view_path = self.parent_ref.resolve(context)
#         if not view_path:
#             seq_view = context.get_context_for_shape(self.parent_ref.get_root_shape()).root_view
#         else:
#             seq_view = path.navigate_view(
#                 context.get_context_for_shape(self.parent_ref.get_root_shape()).root_view,
#                 view_path,
#             )

#         if not isinstance(seq_view, Sizeable):
#             raise TypeError(f"View {seq_view.__class__.__name__} does not support len()")

#         seq_len = len(seq_view)

#         # Use slice.indices() to properly compute start, stop, step
#         start, stop, step = slice(self.slice_start, self.slice_stop, self.slice_step).indices(
#             seq_len
#         )

#         # Compute slice length
#         if step > 0:
#             slice_len = max(0, (stop - start + step - 1) // step)
#         else:
#             slice_len = max(0, (stop - start + step + 1) // step)

#         # Handle negative index
#         if rel_idx < 0:
#             rel_idx = slice_len + rel_idx

#         # Bounds check
#         if rel_idx < 0 or rel_idx >= slice_len:
#             raise IndexError(
#                 f"slice index {self.relative_index} out of range for slice of length {slice_len}"
#             )

#         return start + rel_idx * step

#     def __repr__(self) -> str:
#         return f"SliceIndexOp(start={self.slice_start}, stop={self.slice_stop}, step={self.slice_step}, idx={self.relative_index})"


# class SequenceSliceRef[T: Value](SequenceRef[T]):
#     """Reference to a slice of a sequence.

#     Represents a range of items in a sequence, supporting operations like extract.

#     Example:
#         class Market(Shape):
#             prices: SequenceRef[float] = ListSlot(float)

#         # Access slice
#         Market.prices[1:5].extract()    # Get items 1-4
#         Market.prices[::2].extract()    # Get every other item
#         Market.prices[1:5][0].get()     # Get first item of slice
#     """

#     slice_start: int | None
#     slice_stop: int | None
#     slice_step: int | None

#     def __init__(
#         self,
#         slice_start: int | None,
#         slice_stop: int | None,
#         slice_step: int | None,
#         item_type: type[T],
#         parent_ref: SequenceRef[T],
#     ) -> None:
#         """Initialize slice reference.

#         Args:
#             slice_start: Start index (None for beginning)
#             slice_stop: Stop index (None for end)
#             slice_step: Step (None for 1)
#             item_type: Python type of items
#             parent_ref: Parent sequence reference
#         """
#         # Initialize parent with empty address - slice is relative to parent
#         super().__init__(
#             address=(),
#             item_type=item_type,
#             view_type=parent_ref.view_type,
#             parent_ref=parent_ref,
#         )
#         self.slice_start = slice_start
#         self.slice_stop = slice_stop
#         self.slice_step = slice_step

#     @overload
#     def __getitem__(self, key: int | RValue[int | Sentinel]) -> SequenceValueRef[T]: ...
#     @overload
#     def __getitem__(self, key: slice) -> SequenceSliceRef[T]: ...

#     def __getitem__(
#         self, key: int | slice | RValue[int | Sentinel]
#     ) -> SequenceValueRef[T] | SequenceSliceRef[T]:
#         """Subscript to get item or sub-slice reference.

#         Args:
#             key: Index or slice relative to this slice

#         Returns:
#             Reference to the item or sub-slice
#         """
#         if isinstance(key, slice):
#             # Create a sub-slice reference with combined slice info
#             # Combine this slice's offset with the new slice
#             new_start = (self.slice_start or 0) + (key.start or 0) * (self.slice_step or 1)
#             new_step = (self.slice_step or 1) * (key.step or 1)
#             # Note: stop is more complex with steps, delegate to parent for now
#             return SequenceSliceRef(
#                 slice_start=new_start,
#                 slice_stop=key.stop,  # This is approximate for sub-slices
#                 slice_step=new_step,
#                 item_type=self.item_type,
#                 parent_ref=self.parent_ref,  # type: ignore[arg-type]
#             )

#         # Compute the actual index using SliceIndexOp
#         return SequenceValueRef(
#             address=SliceIndexOp(
#                 slice_start=self.slice_start,
#                 slice_stop=self.slice_stop,
#                 slice_step=self.slice_step,
#                 relative_index=key,  # type: ignore[arg-type]
#                 parent_ref=self.parent_ref,  # type: ignore[arg-type]
#             ),
#             value_type=self.item_type,
#             parent_ref=self,
#         )

#     def extract(self) -> SliceExtractOp[T]:  # type: ignore
#         """Create extract operation for the slice.

#         Returns:
#             SliceExtractOp that reads the slice
#         """
#         return SliceExtractOp(self)

#     def resolve(self, context: Context) -> path.PathToView:
#         """Resolve to parent's path - slice is transparent in path resolution.

#         The slice ref doesn't add a path segment; it delegates to the parent
#         sequence ref since the slice is a virtual view over the parent.

#         Args:
#             context: Execution context

#         Returns:
#             Path to the parent sequence view
#         """
#         # Delegate to parent - slice doesn't add to path
#         return self.parent_ref.resolve(context)  # type: ignore[union-attr]


# class SequenceShapeSliceRef[T: Shape](SequenceShapeRef[T]):
#     """Reference to a slice of a sequence of shapes.

#     Represents a range of shape items in a sequence.

#     Example:
#         class Market(Shape):
#             orders: SequenceShapeRef[Order] = ShapesListSlot(Order)

#         # Access slice
#         Market.orders[1:5].extract()    # Get orders 1-4 as dicts
#         Market.orders[::2].extract()    # Get every other order
#         Market.orders[1:5][0].id.get()  # Get first order's id in slice
#     """

#     slice_start: int | None
#     slice_stop: int | None
#     slice_step: int | None

#     def __init__(
#         self,
#         slice_start: int | None,
#         slice_stop: int | None,
#         slice_step: int | None,
#         shape_type: type[T],
#         parent_ref: SequenceShapeRef[T],
#     ) -> None:
#         """Initialize shape slice reference.

#         Args:
#             slice_start: Start index (None for beginning)
#             slice_stop: Stop index (None for end)
#             slice_step: Step (None for 1)
#             shape_type: Shape class for items
#             parent_ref: Parent sequence reference
#         """
#         # Initialize parent with empty address - slice is relative to parent
#         super().__init__(
#             address=(),
#             shape_type=shape_type,
#             view_type=parent_ref.view_type,
#             parent_ref=parent_ref,
#         )
#         self.slice_start = slice_start
#         self.slice_stop = slice_stop
#         self.slice_step = slice_step

#     @overload
#     def __getitem__(self, index: int | RValue[int]) -> T: ...
#     @overload
#     def __getitem__(self, index: slice) -> SequenceShapeSliceRef[T]: ...

#     def __getitem__(self, index: int | slice | RValue[int]) -> T | SequenceShapeSliceRef[T]:
#         """Subscript to get shape at index or sub-slice.

#         Args:
#             index: Index or slice relative to this slice

#         Returns:
#             ShapeRef to the item, or SequenceShapeSliceRef for sub-slice
#         """
#         if isinstance(index, slice):
#             # Create a sub-slice reference with combined slice info
#             new_start = (self.slice_start or 0) + (index.start or 0) * (self.slice_step or 1)
#             new_step = (self.slice_step or 1) * (index.step or 1)
#             return SequenceShapeSliceRef(
#                 slice_start=new_start,
#                 slice_stop=index.stop,
#                 slice_step=new_step,
#                 shape_type=self.shape_type,
#                 parent_ref=self.parent_ref,  # type: ignore[arg-type]
#             )

#         from ..views import DictView

#         # Compute the actual index using SliceIndexOp
#         return ShapeRef(
#             address=SliceIndexOp(
#                 slice_start=self.slice_start,
#                 slice_stop=self.slice_stop,
#                 slice_step=self.slice_step,
#                 relative_index=index,
#                 parent_ref=self.parent_ref,  # type: ignore[arg-type]
#             ),
#             shape_type=self.shape_type,
#             view_type=DictView,
#             parent_ref=self,
#         )  # type: ignore[return-value]

#     def extract(self) -> ShapeSliceExtractOp[T]:  # type: ignore
#         """Create extract operation for the slice.

#         Returns:
#             ShapeSliceExtractOp that reads the slice as list of dicts
#         """
#         return ShapeSliceExtractOp(self)

#     def resolve(self, context: Context) -> path.PathToView:
#         """Resolve to parent's path - slice is transparent in path resolution.

#         The slice ref doesn't add a path segment; it delegates to the parent
#         sequence ref since the slice is a virtual view over the parent.

#         Args:
#             context: Execution context

#         Returns:
#             Path to the parent sequence view
#         """
#         # Delegate to parent - slice doesn't add to path
#         return self.parent_ref.resolve(context)  # type: ignore[union-attr]
