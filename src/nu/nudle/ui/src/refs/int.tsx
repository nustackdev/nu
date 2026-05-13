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
	const value = useStore((s) => (s.refs[path]?.value as number) ?? 0);
	return <span className="font-mono text-2xl">{value}</span>;
}

export const IntRef: RefEntry = { factory, component: IntView };
