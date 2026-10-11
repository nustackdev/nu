// Node story harness: draw a registered node type the way a program would.
//
// A node story does not render a component with props. It writes chains into
// the real tree store, the same `write` a frame from Python lands as, then
// draws the root with `NodeView`, so what is on screen is what nudle shows:
// the registry lookup, the flow each container hands down, the handlers.
//
//   <NodeStage root="list-strings" chains={[...]} frames={[...]} />
//
// `chains` are written in order (a chain per node, root-first, as Python's
// `(segment, type, props)` levels), then `frames` are dispatched through the
// store, which is how to show a node after an `append` or a `set_title`.
//
// Every story uses its own root segment. The store is one per page, shared
// by every story Storybook has mounted, so two stories on one root would
// draw into each other. A stage clears its root and rewrites it on mount.
//
// NodeStage draws inside the kitchen sink ThemePair, light and dark side by
// side. A node that portals to <body> (Modal, Sheet) escapes the dark
// column, so it renders alone in a hidden story with NodeSolo, and the
// visible story frames that one per theme with FramePair (see
// ../kitchen-sink/overlays.stories.tsx for the pattern).

import type { ChainStep, Props, TreeFrame } from "@nustackdev/ui-core";
import type * as React from "react";
import { useState } from "react";
import { NodeView, tree } from "../../tree";
import "../../nodes";
import { ThemePair } from "../kitchen-sink/frame";

export { FramePair, SinkPage, sinkParameters } from "../kitchen-sink/frame";

export type NodeSeed = {
	/** The root segment this story owns. Unique per story. */
	root: string;
	/** Chains to write, in order, each root-first. Every one starts at `root`. */
	chains: ChainStep[][];
	/** Frames to dispatch after the chains (an append, a chrome op, ...). */
	frames?: TreeFrame[];
};

/** One chain level, spelled the way Python ships it. */
export function step(segment: string, type: string, props: Props = {}): ChainStep {
	return [segment, type, props];
}

/** Clear `root` and write the seed into the store. Idempotent, so safe under StrictMode. */
export function seed({ root, chains, frames = [] }: NodeSeed): void {
	const store = tree.getState();
	store.remove([root]);
	for (const chain of chains) store.write(chain);
	for (const frame of frames) store.dispatch(frame);
}

// Seeds once, before the first render, so the first paint already has the
// tree and a screenshot never catches it empty.
function useSeed(s: NodeSeed): void {
	useState(() => {
		seed(s);
		return true;
	});
}

/** The seeded root, light and dark side by side. The default node story. */
export function NodeStage({
	label,
	...s
}: NodeSeed & {
	/** Optional caption over each column, e.g. what the story shows. */
	label?: string;
}) {
	useSeed(s);
	return (
		<ThemePair>
			<Stage label={label}>
				<NodeView path={[s.root]} />
			</Stage>
		</ThemePair>
	);
}

/** The seeded root alone, for a hidden story a FramePair frames once per theme. */
export function NodeSolo(s: NodeSeed) {
	useSeed(s);
	return (
		<div className="min-h-screen bg-bg-canvas p-8 text-text-primary">
			<NodeView path={[s.root]} />
		</div>
	);
}

function Stage({ label, children }: { label?: string; children: React.ReactNode }) {
	return (
		<div className="flex flex-col gap-3">
			{label ? <div className="font-mono text-text-muted text-xs">{label}</div> : null}
			{children}
		</div>
	);
}
