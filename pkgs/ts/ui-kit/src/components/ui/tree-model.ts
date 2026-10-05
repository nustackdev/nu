// The tree's model: pure functions over a tree the app owns.
//
// The kit never holds the tree. The app hands it a `TreeSource` (the top-level
// keys, and how to get a key's children, in order) and the kit reads it. What
// a key stands for (a file, a Plane, a JSON path) is the app's business.
//
// The tree is flattened into the rows the fold state shows before anything is
// drawn. Off a flat list every cross-row question (what is below me, who is my
// parent, where would a drop land) is an index away, which is what the
// keyboard and the drag stand on. Recursion makes all of them hard.

/** The app's tree, as the kit reads it. */
export type TreeSource = {
	/** Top-level keys, in order. */
	roots: readonly string[];
	/** A key's children, in order. Empty for a leaf. */
	childrenOf: (key: string) => readonly string[];
};

/** One visible line of the tree, in render order. */
export type TreeRow = {
	key: string;
	/** 0 at the top level. */
	depth: number;
	/** The parent's key, null at the top level. */
	parent: string | null;
	/** 1-based position among its siblings, which is what aria-posinset means. */
	pos: number;
	/** Number of siblings, for aria-setsize. */
	size: number;
	hasChildren: boolean;
	expanded: boolean;
};

/** Where a dragged row would land, against the row under the pointer. */
export type DropEdge = "before" | "after" | "into";

/** A drop target. `key` null is the space below the rows: the top level, last. */
export type DropTarget = { key: string | null; edge: DropEdge };

/** What a drop asks for: `key` under `parent` (null: top level) at `index`. */
export type TreeMove = {
	key: string;
	parent: string | null;
	/** Position among the parent's children, counted without `key`. */
	index: number;
};

function kids(source: TreeSource, parent: string | null): readonly string[] {
	return parent === null ? source.roots : source.childrenOf(parent);
}

/** Walk the tree into the rows `expanded` shows. */
export function flattenTree(source: TreeSource, expanded: ReadonlySet<string>): TreeRow[] {
	const out: TreeRow[] = [];
	const walk = (keys: readonly string[], depth: number, parent: string | null) => {
		keys.forEach((key, i) => {
			const children = source.childrenOf(key);
			const open = expanded.has(key);
			out.push({
				key,
				depth,
				parent,
				pos: i + 1,
				size: keys.length,
				hasChildren: children.length > 0,
				expanded: open,
			});
			if (open) walk(children, depth + 1, key);
		});
	};
	walk(source.roots, 0, null);
	return out;
}

/** A key and every key under it. */
export function subtreeOf(source: TreeSource, key: string): string[] {
	const out = [key];
	for (const kid of source.childrenOf(key)) out.push(...subtreeOf(source, kid));
	return out;
}

/**
 * The edge a pointer at `y` picks on a row spanning `top` to `top + height`:
 * the top quarter is before it, the bottom quarter after, the middle into.
 */
export function dropEdge(top: number, height: number, y: number): DropEdge {
	const at = y - top;
	if (at < height / 4) return "before";
	if (at > (height * 3) / 4) return "after";
	return "into";
}

/**
 * Where dropping `key` on `target` puts it, or null when it would not move or
 * cannot go there (into its own subtree, itself included).
 *
 *   before    as the target's sibling, just above it
 *   into      as the target's last child
 *   after     as the target's sibling, just below it; but as its first child
 *             when the target is open with children showing, since that is
 *             what sits right under the line
 *   key null  the top level, last
 */
export function dropMove(
	source: TreeSource,
	rows: readonly TreeRow[],
	key: string,
	target: DropTarget,
): TreeMove | null {
	if (target.key !== null && subtreeOf(source, key).includes(target.key)) return null;
	const without = (parent: string | null) => kids(source, parent).filter((k) => k !== key);
	const row = target.key === null ? undefined : rows.find((r) => r.key === target.key);

	let parent: string | null;
	let index: number;
	if (!row) {
		parent = null;
		index = without(null).length;
	} else if (target.edge === "into") {
		parent = row.key;
		index = without(row.key).length;
	} else if (target.edge === "after" && row.expanded && row.hasChildren) {
		parent = row.key;
		index = 0;
	} else {
		parent = row.parent;
		const sibs = without(parent);
		const at = sibs.indexOf(row.key);
		index = at < 0 ? sibs.length : target.edge === "after" ? at + 1 : at;
	}

	const from = rows.find((r) => r.key === key)?.parent ?? null;
	if (from === parent && kids(source, parent).indexOf(key) === index) return null;
	return { key, parent, index };
}
