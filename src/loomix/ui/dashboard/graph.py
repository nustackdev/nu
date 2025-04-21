"""
Graph rendering utilities.

This module provides the GraphRenderer class which handles the conversion of
workflow DAGs to visual representations using Graphviz.
"""

import time
from typing import Any, Dict, Optional, Union

import graphviz
import networkx as nx

from loomix.ui.theme import DefaultTheme, Theme


class GraphRenderer:
    """
    Renders workflow DAGs as Graphviz visualizations.

    This class provides utilities for converting Loomi operation DAGs into
    visual representations using the Graphviz library.

    Attributes:
        theme: A Theme instance with styling options
    """

    def __init__(self, theme: Optional[Theme] = None):
        """
        Initialize the renderer with an optional custom theme.

        Args:
            theme: Optional custom styling theme
        """
        self.theme = theme or DefaultTheme()

    def render_graph(
        self,
        graph_data: Union[Dict[str, Any], nx.DiGraph],
        operations_data: Dict[str, Any],
        execution_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        selected_node: Optional[str] = None,
    ) -> graphviz.Digraph:
        """
        Render a DAG with current execution state.

        Args:
            graph_data: Either a dictionary of graph data or a NetworkX DiGraph
            operations_data: Data about completed operations
            execution_data: Data about currently executing operations
            metadata: Optional display metadata for operations
            selected_node: Optional ID of a node to highlight

        Returns:
            Graphviz diagram representing the workflow
        """
        # Create Graphviz diagram
        g = graphviz.Digraph()

        # Set graph attributes correctly
        g.graph_attr.update(self.theme.graph_attrs)

        # Convert NetworkX graph to dictionary format if needed
        if isinstance(graph_data, nx.DiGraph):
            graph_dict = self._convert_networkx_to_dict(graph_data)
        else:
            graph_dict = graph_data

        # Add nodes to the graph
        for op_id, op_info in graph_dict.items():
            self._render_node(
                g, op_id, op_info, operations_data, execution_data, metadata, selected_node
            )

        # Add edges to the graph
        self._render_edges(g, graph_dict, operations_data, selected_node)

        return g

    def _render_node(
        self,
        graph: graphviz.Digraph,
        node_id: str,
        node_info: Dict[str, Any],
        operations_data: Dict[str, Any],
        execution_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        selected_node: Optional[str] = None,
    ) -> None:
        """
        Render a single node in the graph.

        Args:
            graph: Graphviz diagram to add the node to
            node_id: ID of the node to render
            node_info: Information about the node
            operations_data: Data about completed operations
            execution_data: Data about currently executing operations
            metadata: Optional display metadata for operations
            selected_node: Optional ID of a node to highlight
        """
        # Determine node status
        status = "pending"
        if node_id in execution_data:
            status = "running"
        elif node_id in operations_data and "status" in operations_data[node_id]:
            status = operations_data[node_id]["status"]

        # Apply style based on status
        style = dict(self.theme.node_styles.get(status, self.theme.node_styles["pending"]))

        # Highlight selected node if specified
        if selected_node and node_id == selected_node:
            style["penwidth"] = "3.0"
            style["color"] = "blue"

        # Create label with timing information if available
        label = node_info.get("name", node_id)

        # Add custom display name from metadata if available
        if metadata and node_id in metadata and "display_name" in metadata[node_id]:
            label = metadata[node_id]["display_name"]

        # Add operation type
        op_type = node_info.get("type", "Unknown")
        label += f" ({op_type})"

        # Add timing information
        if (
            status == "running"
            and node_id in execution_data
            and "start_time" in execution_data[node_id]
        ):
            start_time = execution_data[node_id]["start_time"]
            elapsed = time.time() - start_time
            label += f"\n{self.theme.timing_format.format(elapsed)}"
        elif (
            status == "completed"
            and node_id in operations_data
            and "duration" in operations_data[node_id]
        ):
            duration = operations_data[node_id]["duration"]
            label += f"\n{self.theme.timing_format.format(duration)}"
        elif (
            status == "error" and node_id in operations_data and "error" in operations_data[node_id]
        ):
            label += "\n⚠ Error"

        # Add the node to the graph
        graph.node(node_id, label=label, **style)

    def _render_edges(
        self,
        graph: graphviz.Digraph,
        graph_data: Dict[str, Any],
        operations_data: Dict[str, Any],
        selected_node: Optional[str] = None,
    ) -> None:
        """
        Render all edges in the graph.

        Args:
            graph: Graphviz diagram to add edges to
            graph_data: Dictionary representation of the graph
            operations_data: Data about completed operations
            selected_node: Optional ID of a node to highlight
        """
        for op_id, op_info in graph_data.items():
            # Process parent-child relationship
            parent_id = op_info.get("parent")
            if parent_id and parent_id in graph_data:
                self._render_edge(
                    graph, parent_id, op_id, graph_data, operations_data, selected_node
                )

            # Process explicit children relationships (if present)
            children = op_info.get("children", [])
            for child_id in children:
                # Skip if already processed through parent relationship
                if (
                    "parent" in graph_data.get(child_id, {})
                    and graph_data[child_id]["parent"] == op_id
                ):
                    continue

                # Only add edge if child exists in graph
                if child_id in graph_data:
                    self._render_edge(
                        graph, op_id, child_id, graph_data, operations_data, selected_node
                    )

    def _render_edge(
        self,
        graph: graphviz.Digraph,
        source_id: str,
        target_id: str,
        graph_data: Dict[str, Any],
        operations_data: Dict[str, Any],
        selected_node: Optional[str] = None,
    ) -> None:
        """
        Render a single edge in the graph.

        Args:
            graph: Graphviz diagram to add the edge to
            source_id: ID of the source node
            target_id: ID of the target node
            graph_data: Dictionary representation of the graph
            operations_data: Data about completed operations
            selected_node: Optional ID of a node to highlight
        """
        # Determine source and target status
        source_status = "pending"
        if source_id in operations_data and "status" in operations_data[source_id]:
            source_status = operations_data[source_id]["status"]

        target_status = "pending"
        if target_id in operations_data and "status" in operations_data[target_id]:
            target_status = operations_data[target_id]["status"]

        # Select edge style based on status
        edge_style = dict(self.theme.edge_styles.get("pending", {}))

        if source_status == "completed" and target_status == "running":
            edge_style = dict(self.theme.edge_styles.get("active", {}))
        elif source_status == "completed" and target_status == "completed":
            edge_style = dict(self.theme.edge_styles.get("completed", {}))
        elif source_status == "error" or target_status == "error":
            edge_style = dict(self.theme.edge_styles.get("error", {}))

        # Highlight edge if either node is selected
        if selected_node and (source_id == selected_node or target_id == selected_node):
            edge_style["penwidth"] = "2.5"
            edge_style["color"] = "blue"

        # Add the edge to the graph
        graph.edge(source_id, target_id, **edge_style)

    def _convert_networkx_to_dict(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """
        Convert a NetworkX DiGraph to a dictionary format compatible with the renderer.

        Args:
            graph: NetworkX directed graph

        Returns:
            Dictionary representation of the graph
        """
        result = {}

        for node in graph.nodes():
            # Get node attributes
            attrs = graph.nodes[node]
            obj = attrs.get("obj", None)

            # Get node name from object if available
            name = obj.__class__.__name__ if obj else str(node)

            # Get node children
            children = list(graph.successors(node))

            # Get node parent (first predecessor)
            parents = list(graph.predecessors(node))
            parent = parents[0] if parents else None

            # Store node in result
            result[str(node)] = {
                "name": name,
                "type": obj.__class__.__name__ if obj else "Unknown",
                "parent": str(parent) if parent else None,
                "children": [str(child) for child in children],
            }

        return result

    def render_operations_dag(
        self,
        root_operation,
        operations_data: Dict[str, Any],
        execution_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        selected_node: Optional[str] = None,
    ) -> graphviz.Digraph:
        """
        Render a DAG directly from Operation objects.

        Args:
            root_operation: The root operation of the DAG
            operations_data: Data about completed operations
            execution_data: Data about currently executing operations
            metadata: Optional display metadata for operations
            selected_node: Optional ID of a node to highlight

        Returns:
            Graphviz diagram representing the workflow
        """
        # Convert operations to graph data dictionary
        graph_data = self._convert_operations_to_dict(root_operation)

        # Render the graph
        return self.render_graph(
            graph_data, operations_data, execution_data, metadata, selected_node
        )

    def _convert_operations_to_dict(self, root_operation) -> Dict[str, Any]:
        """
        Convert an operation hierarchy to a dictionary format compatible with the renderer.

        Args:
            root_operation: The root operation to convert

        Returns:
            Dictionary representation of the operation DAG
        """
        result = {}
        visited = set()

        def process_operation(operation, parent_id=None):
            # Skip if already visited
            op_id = operation.key()
            if op_id in visited:
                return

            visited.add(op_id)

            # Get operation metadata
            op_type = operation.__class__.__name__
            op_name = operation.metadata.name if hasattr(operation, "metadata") else op_type

            # Add operation to result
            result[op_id] = {
                "name": op_name,
                "type": op_type,
                "parent": parent_id,
                "children": [],
            }

            # Add to parent's children if applicable
            if parent_id and parent_id in result:
                result[parent_id]["children"].append(op_id)

            # Process children
            for child in operation.children:
                process_operation(child, op_id)

        # Start with root operation
        process_operation(root_operation)

        return result

    def render_from_networkx(
        self,
        graph: nx.DiGraph,
        operations_data: Dict[str, Any],
        execution_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        selected_node: Optional[str] = None,
    ) -> graphviz.Digraph:
        """
        Render a DAG from a NetworkX DiGraph.

        Args:
            graph: NetworkX directed graph
            operations_data: Data about completed operations
            execution_data: Data about currently executing operations
            metadata: Optional display metadata for operations
            selected_node: Optional ID of a node to highlight

        Returns:
            Graphviz diagram representing the workflow
        """
        return self.render_graph(graph, operations_data, execution_data, metadata, selected_node)
