// LensRef -- a Shape browsed as cascading columns.
//
// Server-owned data, browser-owned cursor. A write carries the whole new state
// as two plain props, `{cursor, columns}`, so the default merge is exactly
// right and this type needs no write handler. A move goes back out as a notify
// carrying the whole new cursor, already resolved by the browser, the same way
// a table's row click goes out as an index.
//
// The cursor is relative to the Shape the program pointed the lens at, and
// nothing here knows where that Shape lives. That is the containment: a
// crafted cursor names a slot on that Shape or it names nothing, and the
// server has no path string to be talked into extending upward.
//
// The columns themselves (rows, keyboard, the reader pane) live in ./lens/ --
// no store coupling, so a host that wants a column browser without a node can
// use it directly.

import { OPS } from "@nustackdev/ui-core";
import { useCallback, useMemo } from "react";
import { type NodeEntry, type NodeProps, useListProp, useNumberProp, useSend } from "../../tree";
import { LensColumns } from "./lens/columns";
import type { Column } from "./lens/types";

const NO_CURSOR: string[] = [];

function LensView({ path }: NodeProps) {
	const rawCursor = useListProp<unknown>(path, "cursor");
	const columns = useListProp<Column>(path, "columns");
	const height = useNumberProp(path, "height", 420);
	const send = useSend(path);

	// The prop keeps its wire name; it is called `cursor` here so it never
	// reads as this node's own address, which is what `path` is.
	const cursor = useMemo(
		() => (rawCursor.length ? rawCursor.map((s) => String(s)) : NO_CURSOR),
		[rawCursor],
	);

	const navigate = useCallback((next: string[]) => send(OPS.notify, next), [send]);

	return <LensColumns columns={columns} cursor={cursor} onNavigate={navigate} height={height} />;
}

export const LensRef: NodeEntry = { component: LensView };
