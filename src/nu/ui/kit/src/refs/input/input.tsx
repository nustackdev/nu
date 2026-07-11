// InputRef -- text input. Browser is source of truth.
//
// User types: local store updates immediately (controlled input).
// On blur or Enter: notify server. Server-initiated read: answer with current
// value. Server-initiated write: replace the value (canonical / reset).
// Class-level defaults (label, placeholder, value, type, max_length) seed the
// slice via mount props.

import { OP_NOTIFY } from "@nustackdev/ui-core";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const factory: SliceFactory = (path, ctx, props) => ({
	type: "InputRef",
	value: typeof props?.value === "string" ? (props.value as string) : "",
	label: typeof props?.label === "string" ? (props.label as string) : "",
	placeholder: typeof props?.placeholder === "string" ? (props.placeholder as string) : "",
	inputType: typeof props?.type === "string" ? (props.type as string) : "text",
	maxLength: typeof props?.max_length === "number" ? (props.max_length as number) : null,
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			// Coerce: a null write (sentinel) must not make the input
			// uncontrolled. Always land a string.
			slice.value = v == null ? "" : String(v);
		}),
	get: () => {
		// Read the current value via a one-shot store inspection. Avoids
		// React stale-closure issues that a closed-over `value` would have.
		const slice = useStore.getState().refs[path];
		return (slice?.value as string) ?? "";
	},
});

function InputView({ path }: { path: string }) {
	const value = useStore((s) => (s.refs[path]?.value as string) ?? "");
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const placeholder = useStore((s) => (s.refs[path]?.placeholder as string) ?? "");
	const inputType = useStore((s) => (s.refs[path]?.inputType as string) ?? "text");
	const maxLength = useStore((s) => s.refs[path]?.maxLength as number | null | undefined);
	const setLocal = useStore((s) => s.setLocal);
	const send = useStore((s) => s.send);
	const commit = () => send({ op: OP_NOTIFY, ref: path, payload: null });
	return (
		<label className="flex flex-col gap-1 text-sm">
			{label && <span className="text-gray-700">{label}</span>}
			<input
				type={inputType}
				placeholder={placeholder}
				maxLength={maxLength ?? undefined}
				className="w-full rounded border px-3 py-2 font-mono text-sm"
				value={value}
				onChange={(e) => setLocal(path, e.target.value)}
				onBlur={commit}
				onKeyDown={(e) => {
					if (e.key === "Enter") {
						commit();
						(e.target as HTMLInputElement).blur();
					}
				}}
			/>
		</label>
	);
}

export const InputRef: RefEntry = { factory, component: InputView };
