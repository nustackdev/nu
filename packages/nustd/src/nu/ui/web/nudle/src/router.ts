// Routing, read off the tree like everything else.
//
// There is no envelope to read routes from any more. A page is a root-level
// node of type "Page" whose `route` and `label` are declared props, so they
// ride the chain onto the node at boot and stay there. The NavRef is another
// root-level node, and it mirrors where the browser actually is in its
// `value`. So the router is a selector, not a second source of truth.
//
// Every hook here returns a string or a shallow-compared string list on
// purpose: the shell re-renders when the active page changes and not when
// something deep inside one of them does.

import { useTree } from "@nustackdev/ui-kit";
import type { TreeNode } from "@nustackdev/ui-core";
import { useShallow } from "zustand/react/shallow";

export const PAGE_TYPE = "Page";
export const NAV_TYPE = "NavRef";

const NONE: string[] = [];

function segmentsOfType(root: TreeNode, type: string): string[] {
	const out: string[] = [];
	for (const [segment, node] of root.children) {
		if (node.type === type) out.push(segment);
	}
	return out.length ? out : NONE;
}

/** Every root-level child, in the order it was written. */
export function useRootSegments(): string[] {
	return useTree(
		useShallow((s) => {
			if (!s.root.children.size) return NONE;
			return [...s.root.children.keys()];
		}),
	);
}

/** The pages, in declaration order. Empty for a single-page app. */
export function usePageSegments(): string[] {
	return useTree(useShallow((s) => segmentsOfType(s.root, PAGE_TYPE)));
}

/** The NavRef's segment, if the app declared one. */
export function useNavSegment(): string | null {
	return useTree((s) => segmentsOfType(s.root, NAV_TYPE)[0] ?? null);
}

/** The page to show: the one whose route the NavRef is on, else the first. */
export function useActivePage(): string | null {
	return useTree((s) => {
		let current: string | undefined;
		let first: string | null = null;
		let match: string | null = null;
		for (const node of s.root.children.values()) {
			if (node.type !== NAV_TYPE) continue;
			const v = node.props.value;
			if (v != null) current = String(v);
			break;
		}
		for (const [segment, node] of s.root.children) {
			if (node.type !== PAGE_TYPE) continue;
			if (first === null) first = segment;
			if (current !== undefined && String(node.props.route ?? "") === current) {
				match = segment;
				break;
			}
		}
		return match ?? first;
	});
}
