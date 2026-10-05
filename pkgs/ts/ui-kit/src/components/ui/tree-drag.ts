// Drag and drop for a tree: reorder, nest and move to the top, all as one
// `TreeMove` handed to the app.
//
// Native HTML5 drag and drop: the browser owns the threshold that tells a drag
// from a click, so a row stays an ordinary row until it is dragged. Only a
// drag that started on one of this tree's rows is taken; anything else dragged
// over it (a file, another tree's row) passes through untouched.
//
// The kit moves nothing. A drop reports where the row would land and the app
// decides; when the tree it hands back has changed, the rows follow.

import type * as React from "react";
import { useCallback, useMemo, useState } from "react";
import {
	type DropTarget,
	dropEdge,
	dropMove,
	subtreeOf,
	type TreeMove,
	type TreeRow,
	type TreeSource,
} from "./tree-model";

/** What a row's drag carries by default: its key. */
export const TREE_MIME = "application/x-nu-tree-key";

export type TreeDragOptions = {
	source: TreeSource;
	rows: readonly TreeRow[];
	onMove: (move: TreeMove) => void;
	/** Whether a row may be picked up. Every row by default. */
	canDrag?: (key: string) => boolean;
	/** The type the key travels under, for drop targets outside the tree. */
	mime?: string;
};

export type TreeDrag = {
	/** The row being dragged, null at rest. */
	dragKey: string | null;
	/** Where it would land right now. */
	target: DropTarget | null;
	/** Handlers for one row. */
	itemProps: (key: string) => React.HTMLAttributes<HTMLElement> & { draggable?: boolean };
	/** Handlers for the space under the last row: a drop there is the top level, last. */
	tailProps: React.HTMLAttributes<HTMLElement>;
	/** Handlers around rows and tail: leaving them drops the mark. */
	leaveProps: React.HTMLAttributes<HTMLElement>;
};

function edgeOf(e: React.DragEvent): ReturnType<typeof dropEdge> {
	const r = (e.currentTarget as HTMLElement).getBoundingClientRect();
	return dropEdge(r.top, r.height, e.clientY);
}

export function useTreeDrag({
	source,
	rows,
	onMove,
	canDrag,
	mime = TREE_MIME,
}: TreeDragOptions): TreeDrag {
	const [dragKey, setDragKey] = useState<string | null>(null);
	const [target, setTarget] = useState<DropTarget | null>(null);

	// The dragged row and everything under it: no drop lands there.
	const barred = useMemo(
		() => new Set(dragKey ? subtreeOf(source, dragKey) : []),
		[source, dragKey],
	);

	const end = useCallback(() => {
		setDragKey(null);
		setTarget(null);
	}, []);

	const drop = useCallback(
		(to: DropTarget) => {
			const key = dragKey;
			end();
			if (!key) return;
			const move = dropMove(source, rows, key, to);
			if (move) onMove(move);
		},
		[dragKey, source, rows, onMove, end],
	);

	const aim = useCallback(
		(to: DropTarget) => {
			if (target?.key !== to.key || target.edge !== to.edge) setTarget(to);
		},
		[target],
	);

	const itemProps = useCallback(
		(key: string) => {
			const draggable = canDrag ? canDrag(key) : true;
			return {
				draggable,
				onDragStart: (e: React.DragEvent) => {
					if (!draggable) return;
					e.dataTransfer.effectAllowed = "move";
					e.dataTransfer.setData(mime, key);
					setDragKey(key);
				},
				onDragEnd: end,
				onDragOver: (e: React.DragEvent) => {
					if (!dragKey) return;
					if (barred.has(key)) {
						if (target) setTarget(null);
						return;
					}
					e.preventDefault();
					e.stopPropagation();
					e.dataTransfer.dropEffect = "move";
					aim({ key, edge: edgeOf(e) });
				},
				onDrop: (e: React.DragEvent) => {
					if (!dragKey || barred.has(key)) return;
					e.preventDefault();
					e.stopPropagation();
					drop({ key, edge: edgeOf(e) });
				},
			};
		},
		[canDrag, mime, dragKey, barred, target, aim, drop, end],
	);

	const tailProps = useMemo(
		() => ({
			onDragOver: (e: React.DragEvent) => {
				if (!dragKey) return;
				e.preventDefault();
				e.dataTransfer.dropEffect = "move";
				aim({ key: null, edge: "after" });
			},
			onDrop: (e: React.DragEvent) => {
				if (!dragKey) return;
				e.preventDefault();
				drop({ key: null, edge: "after" });
			},
		}),
		[dragKey, aim, drop],
	);

	const leaveProps = useMemo(
		() => ({
			onDragLeave: (e: React.DragEvent) => {
				if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setTarget(null);
			},
		}),
		[],
	);

	return { dragKey, target, itemProps, tailProps, leaveProps };
}
