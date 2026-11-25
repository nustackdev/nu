// LensRef -- a Shape browsed as cascading columns.
//
// Server-owned data, browser-owned cursor. A write carries the whole new state
// as two plain props, `{cursor, columns}`. A move goes back out as
// `{event: "change", value: cursor}`, the whole new cursor already resolved by
// the browser.
//
// The cursor that is read back is `value`: where the person last moved to, or
// the cursor the server last wrote, whichever came later. It is kept apart from
// the `cursor` prop on purpose: `cursor` is what the drawn columns belong to,
// and it only moves when the cascade for it lands, so the trail never runs
// ahead of the columns it describes.
//
// The cursor is relative to the Shape the program pointed the lens at, and
// nothing here knows where that Shape lives. That is the containment: a
// crafted cursor names a slot on that Shape or it names nothing, and the
// server has no path string to be talked into extending upward.
//
// The columns themselves (rows, keyboard, the reader pane) live in ./lens/ --
// no store coupling, so a host that wants a column browser without a node can
// use it directly.

import { useCallback, useMemo } from "react";
import {
	EVENTS,
	type NodeEntry,
	type NodeProps,
	useEmit,
	useListProp,
	useNumberProp,
	useSetValue,
} from "../../tree";
import { LensColumns } from "./lens/columns";
import type { Column } from "./lens/types";

const NO_CURSOR: string[] = [];

function LensView({ path }: NodeProps) {
	const rawCursor = useListProp<unknown>(path, "cursor");
	const columns = useListProp<Column>(path, "columns");
	const height = useNumberProp(path, "height", 420);
	const emit = useEmit(path);
	const setValue = useSetValue(path);

	// The prop keeps its wire name; it is called `cursor` here so it never
	// reads as this node's own address, which is what `path` is.
	const cursor = useMemo(
		() => (rawCursor.length ? rawCursor.map((s) => String(s)) : NO_CURSOR),
		[rawCursor],
	);

	const navigate = useCallback(
		(next: string[]) => {
			setValue(next);
			emit(EVENTS.change, { value: next });
		},
		[setValue, emit],
	);

	return <LensColumns columns={columns} cursor={cursor} onNavigate={navigate} height={height} />;
}

/** The cursor read back: the last move, or the last cursor written. */
function readCursor(props: Record<string, unknown>): string[] {
	const raw = props.value ?? props.cursor;
	return Array.isArray(raw) ? raw.map((s) => String(s)) : [];
}

export const LensRef: NodeEntry = {
	component: LensView,
	fill: true,
	handlers: {
		// A write is the default merge, plus the cursor it ships becomes the one
		// read back: the server moved the lens, so that is where it is now.
		write: (ctx, payload) => {
			if (payload == null || typeof payload !== "object") return;
			const next = payload as Record<string, unknown>;
			ctx.update((props) => {
				Object.assign(props, next);
				if ("cursor" in next) props.value = next.cursor;
			});
		},
	},
	reads: { "": readCursor },
};
