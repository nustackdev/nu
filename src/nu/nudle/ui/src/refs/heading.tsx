// HeadingRef -- display-only string, renders as <h1>. Body slot.

import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

const factory: SliceFactory = (path, ctx) => ({
	type: "HeadingRef",
	value: "",
	write: (v) =>
		ctx.set((refs) => {
			refs[path].value = v as string;
		}),
});

function HeadingView({ path }: { path: string }) {
	const value = useStore((s) => (s.refs[path]?.value as string) ?? "");
	return <h1 className="text-3xl font-semibold">{value}</h1>;
}

export const HeadingRef: RefEntry = { factory, component: HeadingView };
