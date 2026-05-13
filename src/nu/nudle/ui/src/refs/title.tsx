// TitleRef -- display-only string, renders as <h1>.

import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

const factory: SliceFactory = (path, ctx) => ({
	type: "TitleRef",
	value: "",
	write: (v) =>
		ctx.set((refs) => {
			refs[path].value = v as string;
		}),
});

function TitleView({ path }: { path: string }) {
	const value = useStore((s) => (s.refs[path]?.value as string) ?? "");
	return <h1 className="text-3xl font-semibold">{value}</h1>;
}

export const TitleRef: RefEntry = { factory, component: TitleView };
