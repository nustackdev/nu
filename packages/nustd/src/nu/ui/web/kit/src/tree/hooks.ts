// React bindings over the tree store.
//
// The granularity that matters: a node's `props` object only changes when
// that node's own props change. Immer copies the spine from the root down to
// whatever was touched, so a parent's `node` and `children` get fresh
// identities when a descendant changes, but its `props` does not. So hooks
// that watch props re-render on the node's own change and nothing else, and
// `useChildren` compares the segment list shallowly so a node appearing
// somewhere else in the tree never re-renders an unrelated parent.

import { useCallback, useMemo } from "react";
import { getNode, type Path, type Props, type TreeNode } from "@nustackdev/ui-core";
import { useShallow } from "zustand/react/shallow";
import { tree, useTree } from "./store";

const NO_PROPS: Props = {};
const NO_CHILDREN: string[] = [];
const NO_ITEMS: unknown[] = [];

/** The node's type and props. Re-renders on this node's own change only. */
export function useNode(path: Path): { type: string | null; props: Props } {
	const key = pathKey(path);
	const type = useTree((s) => getNode(s.root, path)?.type ?? null);
	const props = useTree((s) => getNode(s.root, path)?.props ?? NO_PROPS);
	return useMemo(
		() => ({ type, props }),
		// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
		[key, type, props],
	);
}

/** Just the props. The common case for a leaf component. */
export function useProps(path: Path): Props {
	return useNode(path).props;
}

/** One prop, with a fallback. Re-renders only when that prop's node changes. */
export function useProp<T>(path: Path, key: string, fallback: T): T {
	const props = useProps(path);
	const v = props[key];
	return v === undefined ? fallback : (v as T);
}

// Props arrive off the wire, so a component reads them the way it wants them
// rather than trusting the writer. These are the three coercions every ported
// ref used to do by hand in its factory.

/** A prop as a string. A null or missing value falls back. */
export function useStringProp(path: Path, key: string, fallback = ""): string {
	const v = useProps(path)[key];
	return v == null ? fallback : String(v);
}

/** A prop as a finite number, or the fallback. */
export function useNumberProp(path: Path, key: string, fallback: number): number {
	const n = Number(useProps(path)[key]);
	return Number.isFinite(n) ? n : fallback;
}

/** A prop as a boolean. Missing falls back; anything else is truthiness. */
export function useBoolProp(path: Path, key: string, fallback = false): boolean {
	const v = useProps(path)[key];
	return v === undefined || v === null ? fallback : Boolean(v);
}

/** A prop as a list. Anything that is not one reads as empty. */
export function useListProp<T>(path: Path, key: string): T[] {
	const v = useProps(path)[key];
	return Array.isArray(v) ? (v as T[]) : (NO_ITEMS as T[]);
}

/** Shorthand for the canonical `value` prop. */
export function useValue<T>(path: Path, fallback: T): T {
	return useProp(path, "value", fallback);
}

/** Whether a node is there at all. */
export function useExists(path: Path): boolean {
	return useTree((s) => getNode(s.root, path) !== null);
}

/** Child segments in insertion order, shallow compared. */
export function useChildren(path: Path): string[] {
	return useTree(
		useShallow((s) => {
			const node = getNode(s.root, path);
			if (!node) return NO_CHILDREN;
			const names = Object.keys(node.children);
			return names.length ? names : NO_CHILDREN;
		}),
	);
}

/** Send a frame from this node. */
export function useSend(path: Path): (op: string, payload?: unknown, id?: string) => void {
	const key = pathKey(path);
	return useCallback(
		(op: string, payload: unknown = null, id?: string) =>
			tree.getState().send({ op, ref: path, payload, id }),
		// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
		[key],
	);
}

/** Merge props into this node locally, without going near the wire. */
export function useSetProps(path: Path): (props: Props) => void {
	const key = pathKey(path);
	return useCallback(
		(props: Props) => tree.getState().setProps(path, props),
		// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
		[key],
	);
}

/** Local edit of the `value` prop. What a controlled input calls as you type. */
export function useSetValue(path: Path): (value: unknown) => void {
	const setProps = useSetProps(path);
	return useCallback((value: unknown) => setProps({ value }), [setProps]);
}

/** Read a node outside of render (event handlers, handlers, effects). */
export function nodeAt(path: Path): TreeNode | null {
	return tree.getState().getIn(path);
}

/** Stable dependency for a path. Segments can hold anything, so join safely. */
export function pathKey(path: Path): string {
	return JSON.stringify(path);
}
