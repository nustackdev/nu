// InputRef -- text input. Browser is source of truth.
//
// User types: local store updates immediately (controlled input).
// On blur: notify server. Server-initiated read: answer with current value.
// Server-initiated write: replace the value (canonical / reset).

import { OP_NOTIFY } from "../protocol";
import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

const factory: SliceFactory = (path, ctx) => ({
	type: "InputRef",
	value: "",
	write: (v) =>
		ctx.set((refs) => {
			refs[path].value = v as string;
		}),
	get: () => {
		// Read the current value via a one-shot store inspection. Avoids
		// React stale-closure issues that a closed-over `value` would have.
		const slice = useStore.getState().refs[path];
		return slice?.value ?? "";
	},
});

function InputView({ path }: { path: string }) {
	const value = useStore((s) => (s.refs[path]?.value as string) ?? "");
	const setLocal = useStore((s) => s.setLocal);
	const send = useStore((s) => s.send);
	return (
		<input
			className="w-full rounded border px-3 py-2 font-mono text-sm"
			value={value}
			onChange={(e) => setLocal(path, e.target.value)}
			onBlur={() => send({ op: OP_NOTIFY, ref: path, payload: null })}
			onKeyDown={(e) => {
				if (e.key === "Enter") {
					send({ op: OP_NOTIFY, ref: path, payload: null });
					(e.target as HTMLInputElement).blur();
				}
			}}
		/>
	);
}

export const InputRef: RefEntry = { factory, component: InputView };
