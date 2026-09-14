// Renders one node by its type, and recurses.
//
// A node with a registered type renders that component, wrapped in an error
// boundary so one throwing renderer cannot blank the page. A node with no
// type (autovivified on the way to something below it) or a type nobody
// registered renders its children instead, so a subtree stays visible even
// when a level in the middle means nothing to the browser.

import type { Path } from "@nustackdev/ui-core";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { useChildren, useNode, pathKey } from "./hooks";
import { componentFor } from "./registry";

export function NodeView({ path }: { path: Path }) {
	const { type } = useNode(path);
	const Comp = componentFor(type);
	if (!Comp) {
		if (type) {
			return (
				<div className="text-xs text-status-danger font-mono">no component for {type}</div>
			);
		}
		return <NodeChildren path={path} />;
	}
	return (
		<ErrorBoundary label={`${path.join(" / ")} (${type})`}>
			<Comp path={path} />
		</ErrorBoundary>
	);
}

/** Every child of a node, in insertion order. What a layout type renders. */
export function NodeChildren({ path }: { path: Path }) {
	const children = useChildren(path);
	return (
		<>
			{children.map((segment) => (
				<NodeView key={segment} path={[...path, segment]} />
			))}
		</>
	);
}

/** One named child, when a type places its slots itself. */
export function ChildView({ path, segment }: { path: Path; segment: string }) {
	return <NodeView key={pathKey([...path, segment])} path={[...path, segment]} />;
}
