// StatusSquaresRef -- a strip of status squares, one per item, capped.
//
// Server-owned. A write is a partial merge of `counts` / `max_items` / `labels` /
// `total` into the node's props, which is the default store behaviour, so
// this type is a component and nothing else. `counts` maps a tone to how
// many items hold it; an unknown tone or a bad count is dropped here, since
// props arrive off the wire. Composes the kit StatusSquares primitive.

import {
	STATUS_SQUARE_TONES,
	type StatusSquareCounts,
	StatusSquares,
	type StatusSquareTone,
} from "../../components/ui/status-squares";
import { type NodeEntry, type NodeProps, useEnumProp, useNumberProp, useProp } from "../../tree";

const TOTALS = ["overflow", "always", "never"] as const;

function pick<T>(
	raw: unknown,
	read: (v: unknown) => T | undefined,
): Partial<Record<StatusSquareTone, T>> {
	const out: Partial<Record<StatusSquareTone, T>> = {};
	if (raw == null || typeof raw !== "object") return out;
	for (const tone of STATUS_SQUARE_TONES) {
		const v = read((raw as Record<string, unknown>)[tone]);
		if (v !== undefined) out[tone] = v;
	}
	return out;
}

const readCount = (v: unknown) => {
	const n = Number(v);
	return Number.isFinite(n) && n > 0 ? n : undefined;
};
const readLabel = (v: unknown) => (v == null || v === "" ? undefined : String(v));

function StatusSquaresView({ path }: NodeProps) {
	const counts: StatusSquareCounts = pick(useProp<unknown>(path, "counts", null), readCount);
	const labels = pick(useProp<unknown>(path, "labels", null), readLabel);
	const maxItems = useNumberProp(path, "max_items", 10);
	const total = useEnumProp(path, "total", TOTALS, "overflow");
	return <StatusSquares counts={counts} maxItems={maxItems} labels={labels} total={total} />;
}

export const StatusSquaresRef: NodeEntry = { component: StatusSquaresView };
