// Renders one node by its type, and recurses.
//
// A node with a registered type renders that component, wrapped in an error
// boundary so one throwing renderer cannot blank the page. A node with no
// type (autovivified on the way to something below it) or a type nobody
// registered renders its children instead, so a subtree stays visible even
// when a level in the middle means nothing to the browser. A hidden node
// (`Ref.hide()`) renders nothing at all, and containers leave it out of
// their children (see `useChildren`), so it takes no cell either.

import type { Path } from "@nustackdev/ui-core";
import type { ComponentType, ReactNode } from "react";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { type Flow, FlowProvider, useFlow } from "./flow";
import { pathKey, useChildren, useHidden, useNode } from "./hooks";
import { componentFor, isFill, registry } from "./registry";

export function NodeView({ path }: { path: Path }) {
	const { type } = useNode(path);
	const hidden = useHidden(path);
	const Comp = componentFor(type);
	if (hidden) return null;
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
 * The default cell in a block flow (Column, Card, Box, Form, ...). A fill
 * child (a chart, an input, a card) stretches to the container's width; a
 * content child (a button, a badge, a key, a line of text) keeps its own
 * width at the start edge instead of being pulled into a full width bar. A
 * type nobody registered is drawn bare and stretches.
 */
export function BlockCell({ path, children }: CellProps) {
	const { type, props } = useNode(path);
	if (!type || !registry[type] || isFill(type, props)) return <>{children}</>;
	return (
		<div data-slot="block-cell" className="flex min-w-0 flex-col items-start">
			{children}
		</div>
	);
}

/** A cell that draws its child bare: the container's own element lays it out. */
export function BareCell({ children }: CellProps) {
	return <>{children}</>;
}

/**
 * Children in index order, for a container that takes children by position
 * (List, Line). Segments that are indices ("0", "1", ...) sort by number
 * among the places indexed children hold; named segments keep their place in
 * write order. So `[2]` written before `[0]` still draws 0 before 2.
 */
export function indexedOrder(segments: readonly string[]): string[] {
	const isIndex = (s: string) => /^\d+$/.test(s);
	const indexed = segments.filter(isIndex).sort((a, b) => Number(a) - Number(b));
	let next = 0;
	return segments.map((s) => (isIndex(s) ? indexed[next++] : s));
}

/**
 * Every child of a node, in insertion order. What a container type renders.
 *
 * `cell` wraps each child, for a container that needs a box per child (a
 * list item, a grid cell, a row slot that fills). Without it a block flow
 * wraps each child in `BlockCell`, and any other flow draws them bare.
 * `indexed` puts indexed children in index order (see `indexedOrder`).
 * `skip` leaves out the segments a type places itself (a card's `media`,
 * a section's `actions`), so what is left is the body.
 */
export function NodeChildren({
	path,
	cell,
	indexed = false,
	skip,
}: {
	path: Path;
	cell?: ComponentType<CellProps>;
	indexed?: boolean;
	skip?: ReadonlySet<string>;
}) {
	const written = useChildren(path);
	const kept = skip ? written.filter((s) => !skip.has(s)) : written;
	const children = indexed ? indexedOrder(kept) : kept;
	const flow = useFlow();
	const Cell = cell ?? (flow === "block" ? BlockCell : undefined);
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

/** The segment a Card's or a Section's header actions sit at. */
export const ACTIONS_SLOT = "actions";

/**
 * One named child placed by its parent (a card's media or footer, a
 * section's actions), in the flow it is handed. A block flow puts it in a
 * `BlockCell`, the same cell a body child gets; a row flow draws it bare, at
 * its own size. A hidden child draws nothing, cell included.
 */
export function SlotView({
	path,
	segment,
	flow = "block",
}: {
	path: Path;
	segment: string;
	flow?: Flow;
}) {
	const child = [...path, segment];
	const hidden = useHidden(child);
	if (hidden) return null;
	return (
		<FlowProvider flow={flow}>
			{flow === "block" ? (
				<BlockCell path={child}>
					<NodeView path={child} />
				</BlockCell>
			) : (
				<NodeView path={child} />
			)}
		</FlowProvider>
	);
}
