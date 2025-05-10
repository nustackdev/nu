"""
Visualization Service for Loomi workflows.

This module provides the VisualizationService which brings together
tracing and rendering capabilities for workflow visualization.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from loomi.attr import UseService
from loomi.interfaces.state.state import (
    AsyncStateProtocol,
    AsyncTreeDictProtocol,
    SyncStateProtocol,
    SyncTreeDictProtocol,
)
from loomi.service import AsyncService
from loomi.spec import Spec, SpecField
from loomistd.state import StateSpec

from .dashboard.graph import GraphRenderer
from .theme import DefaultTheme, Theme


class VisualizationService(AsyncService):
    """
    Service for visualizing workflow execution.

    This service combines tracing data access with rendering capabilities
    to provide a complete visualization solution.

    Attributes:
        state: Injected state service
        theme: Theme configuration for visualizations
        tracing_path: Path in state where tracing data is stored
    """

    state: AsyncStateProtocol | SyncStateProtocol = UseService()

    spec: VisualizationServiceSpec

    async def setup(self) -> None:
        """Initialize the visualization service."""
        if self.spec.theme == "default":
            # Use default theme if not specified
            self.theme = DefaultTheme()
        else:
            raise TypeError(
                f"Invalid theme specified: {self.spec.theme}. Please use 'default' or a custom theme."
            )

        self.tracing_path = self.spec.tracing_path
        self.graph_renderer = GraphRenderer(self.theme)
        self.last_refresh = datetime.now()
        self.tracing_data = {
            "operations": {},
            "execution": {},
            "graph": {},
            "metadata": {},
        }

    async def cleanup(self) -> None:
        """Clean up the visualization service."""
        pass

    async def load_tracing_data(self) -> Dict[str, Any]:
        """
        Load tracing data from state.

        Returns:
            Dictionary containing tracing data
        """
        # Get tracing data root
        tracing_data = {
            "operations": {},
            "execution": {},
            "graph": {},
            "metadata": {},
        }

        try:
            # Get dictionaries based on state protocol
            ops_dict = None
            exec_dict = None
            graph_dict = None
            meta_dict = None
            root_dict = None

            if isinstance(self.state, AsyncStateProtocol):
                ops_dict = await self.state.dict(*self.tracing_path, "operations")
                exec_dict = await self.state.dict(*self.tracing_path, "execution")
                graph_dict = await self.state.dict(*self.tracing_path, "graph")
                meta_dict = await self.state.dict(*self.tracing_path, "metadata")
                root_dict = await self.state.dict(*self.tracing_path)
            elif isinstance(self.state, SyncStateProtocol):
                ops_dict = self.state.dict(*self.tracing_path, "operations")
                exec_dict = self.state.dict(*self.tracing_path, "execution")
                graph_dict = self.state.dict(*self.tracing_path, "graph")
                meta_dict = self.state.dict(*self.tracing_path, "metadata")
                root_dict = self.state.dict(*self.tracing_path)
            else:
                # Unsupported state protocol
                self.last_refresh = datetime.now()
                return tracing_data

            # Load operations data based on dict protocol
            if isinstance(ops_dict, AsyncTreeDictProtocol):
                tracing_data["operations"] = await ops_dict.to_dict()
            elif isinstance(ops_dict, SyncTreeDictProtocol):
                tracing_data["operations"] = ops_dict.to_dict()

            # Load execution data based on dict protocol
            if isinstance(exec_dict, AsyncTreeDictProtocol):
                tracing_data["execution"] = await exec_dict.to_dict()
            elif isinstance(exec_dict, SyncTreeDictProtocol):
                tracing_data["execution"] = exec_dict.to_dict()

            # Load graph data based on dict protocol
            if isinstance(graph_dict, AsyncTreeDictProtocol):
                tracing_data["graph"] = await graph_dict.to_dict()
            elif isinstance(graph_dict, SyncTreeDictProtocol):
                tracing_data["graph"] = graph_dict.to_dict()

            # Load metadata based on dict protocol
            if isinstance(meta_dict, AsyncTreeDictProtocol):
                tracing_data["metadata"] = await meta_dict.to_dict()
            elif isinstance(meta_dict, SyncTreeDictProtocol):
                tracing_data["metadata"] = meta_dict.to_dict()

            # Get execution summary if available based on dict protocol
            if isinstance(root_dict, AsyncTreeDictProtocol):
                summary = await root_dict.get("execution_summary")
                if summary:
                    tracing_data["summary"] = summary  # type: ignore
            elif isinstance(root_dict, SyncTreeDictProtocol):
                summary = root_dict.get("execution_summary")
                if summary:
                    tracing_data["summary"] = summary  # type: ignore

            self.last_refresh = datetime.now()
            self.tracing_data = tracing_data

        except Exception as e:
            # Handle errors gracefully
            print(f"Error loading tracing data: {e}")

        return tracing_data

    def get_renderer(self) -> GraphRenderer:
        """
        Get the graph renderer.

        Returns:
            GraphRenderer instance
        """
        return self.graph_renderer

    async def render_graph(self, selected_node: Optional[str] = None) -> Any:
        """
        Render the workflow graph.

        Args:
            selected_node: Optional ID of a node to highlight

        Returns:
            Graphviz diagram representing the workflow
        """
        # Ensure data is loaded
        await self.load_tracing_data()

        # Render the graph
        return self.graph_renderer.render_graph(
            self.tracing_data["graph"],
            self.tracing_data["operations"],
            self.tracing_data["execution"],
            self.tracing_data["metadata"],
            selected_node,
        )

    async def get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """
        Get status information for a specific operation.

        Args:
            operation_id: ID of the operation

        Returns:
            Dictionary with operation status information
        """
        # Ensure data is loaded
        await self.load_tracing_data()

        # Check if operation is currently executing
        if operation_id in self.tracing_data["execution"]:
            return self.tracing_data["execution"][operation_id]

        # Check in completed operations
        if operation_id in self.tracing_data["operations"]:
            return self.tracing_data["operations"][operation_id]

        # Check if operation exists in graph
        if operation_id in self.tracing_data["graph"]:
            return {
                "status": "pending",
                "op_name": self.tracing_data["graph"][operation_id].get("name", "Unknown"),
                "op_type": self.tracing_data["graph"][operation_id].get("type", "Unknown"),
            }

        return {"status": "unknown"}

    async def get_execution_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about workflow execution.

        Returns:
            Dictionary with execution statistics
        """
        # Ensure data is loaded
        await self.load_tracing_data()

        # If summary is available, return it
        if "summary" in self.tracing_data:
            return self.tracing_data["summary"]

        # Calculate statistics
        total = len(self.tracing_data["graph"])
        running = len(self.tracing_data["execution"])
        completed = sum(
            1 for op in self.tracing_data["operations"].values() if op.get("status") == "completed"
        )
        failed = sum(
            1 for op in self.tracing_data["operations"].values() if op.get("status") == "error"
        )
        pending = total - running - completed - failed

        # Calculate timing statistics if available
        total_duration = 0
        min_duration = float("inf")
        max_duration = 0
        operation_durations = []

        for op in self.tracing_data["operations"].values():
            if "duration" in op:
                duration = op["duration"]
                total_duration += duration
                min_duration = min(min_duration, duration)
                max_duration = max(max_duration, duration)
                operation_durations.append(duration)

        avg_duration = total_duration / len(operation_durations) if operation_durations else 0
        if min_duration == float("inf"):
            min_duration = 0

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "timing": {
                "total": total_duration,
                "average": avg_duration,
                "min": min_duration,
                "max": max_duration,
            },
        }

    def get_theme(self) -> Theme:
        """
        Get the current theme.

        Returns:
            Current Theme instance
        """
        return self.theme

    def get_last_refresh(self) -> datetime:
        """
        Get the timestamp of the last data refresh.

        Returns:
            Datetime of the last refresh
        """
        return self.last_refresh


class VisualizationServiceSpec(Spec):
    """
    Specification for the Loomi visualization service.

    Attributes:
        state_spec: State specification to use
        tracing_path: Path in state where tracing data is stored
        theme: Theme configuration for visualizations
        streamlit_title: Title for Streamlit app
        streamlit_icon: Icon for Streamlit app
    """

    name: str = SpecField(default="visualization_service")
    factory: type = SpecField(default=VisualizationService)
    state: Spec = SpecField(default_factory=StateSpec)
    tracing_path: tuple[str, ...] = SpecField(default=("_", "tracing"))
    theme: Literal["default"] = SpecField(default="default")
    streamlit_title: str = SpecField(default="Loomi Dashboard")
    streamlit_icon: str = SpecField(default="🔄")
    streamlit_layout: str = SpecField(default="wide")
