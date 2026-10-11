// Renders one node by its type, and recurses.
//
// A node with a registered type renders that component, wrapped in an error
// boundary so one throwing renderer cannot blank the page. A node with no
// type (autovivified on the way to something below it) or a type nobody
// registered renders its children instead, so a subtree stays visible even
// when a level in the middle means nothing to the browser.

import type { Path } from "@nustackdev/ui-core";
import type { ComponentType, ReactNode } from "react";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { pathKey, useChildren, useNode } from "./hooks";
import { componentFor } from "./registry";

export function NodeView({ path }: { path: Path }) {
	const { type } = useNode(path);
	const Comp = componentFor(type);
	if (!Comp) {
		if (type) {
			return <div className="text-xs text-status-danger font-mono">no component for {type}</div>;
		}
		return <NodeChildren path={path} />;
	}
	return (
		<ErrorBoundary label={`${path.join(" / ")} (${type})`}>
			<Comp path={path} />
		</ErrorBoundary>
	);
}

/** What a container wraps each child in: the child's path, and the child drawn. */
export type CellProps = { path: Path; children: ReactNode };

/**
 * Every child of a node, in insertion order. What a container type renders.
 *
 * `cell` wraps each child, for a container that needs a box per child (a
 * list item, a grid cell, a row slot that fills). Without it the children
 * are drawn bare, side by side in the container's own element.
 */
export function NodeChildren({
	path,
	cell: Cell,
}: {
	path: Path;
	cell?: ComponentType<CellProps>;
}) {
	const children = useChildren(path);
	return (
		<>
			{children.map((segment) => {
				const child = [...path, segment];
				if (!Cell) return <NodeView key={segment} path={child} />;
				return (
					<Cell key={segment} path={child}>
						<NodeView path={child} />
					</Cell>
				);
			})}
		</>
	);
}

/** One named child, when a type places its slots itself. */
export function ChildView({ path, segment }: { path: Path; segment: string }) {
	return <NodeView key={pathKey([...path, segment])} path={[...path, segment]} />;
}
