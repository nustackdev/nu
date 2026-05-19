// IntRef -- display-only integer cell, renders as <span>.

import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

const factory: SliceFactory = (path, ctx) => ({
	type: "IntRef",
	value: 0,
	write: (v) =>
		ctx.set((refs) => {
			refs[path].value = v as number;
		}),
});

function IntView({ path }: { path: string }) {
	// A null value (sentinel) renders as a dash, not a thrown render.
	const value = useStore((s) => s.refs[path]?.value);
	const text = typeof value === "number" ? String(value) : value == null ? "-" : String(value);
	return <span className="font-mono text-2xl">{text}</span>;
}

export const IntRef: RefEntry = { factory, component: IntView };
