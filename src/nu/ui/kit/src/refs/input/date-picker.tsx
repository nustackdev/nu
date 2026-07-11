// DatePickerRef -- native single date input. Browser is source of truth.
//
// User picks a date: local store updates and notify fires on the native
// `change` event (commit only, no per-keystroke notify). Server-initiated
// read: answer with current ISO value. Server-initiated write: replace.
// Class-level defaults (label, placeholder, min, max, default) seed the
// slice via mount props; `default` seeds `value`.

import { OP_NOTIFY } from "@nustackdev/ui-core";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const factory: SliceFactory = (path, ctx, props) => ({
	type: "DatePickerRef",
	value: typeof props?.default === "string" ? (props.default as string) : "",
	label: typeof props?.label === "string" ? (props.label as string) : "",
	placeholder: typeof props?.placeholder === "string" ? (props.placeholder as string) : "",
	min: typeof props?.min === "string" ? (props.min as string) : "",
	max: typeof props?.max === "string" ? (props.max as string) : "",
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			slice.value = v == null ? "" : String(v);
		}),
	get: () => {
		const slice = useStore.getState().refs[path];
		return (slice?.value as string) ?? "";
	},
});

function DatePickerView({ path }: { path: string }) {
	const value = useStore((s) => (s.refs[path]?.value as string) ?? "");
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const placeholder = useStore((s) => (s.refs[path]?.placeholder as string) ?? "");
	const min = useStore((s) => (s.refs[path]?.min as string) ?? "");
	const max = useStore((s) => (s.refs[path]?.max as string) ?? "");
	const setLocal = useStore((s) => s.setLocal);
	const send = useStore((s) => s.send);
	return (
		<label className="flex flex-col gap-1 text-sm">
			{label && <span className="text-gray-700">{label}</span>}
			<input
				type="date"
				placeholder={placeholder}
				min={min || undefined}
				max={max || undefined}
				className="w-full rounded border px-3 py-2 font-mono text-sm"
				value={value}
				onChange={(e) => {
					setLocal(path, e.target.value);
					send({ op: OP_NOTIFY, ref: path, payload: null });
				}}
			/>
		</label>
	);
}

export const DatePickerRef: RefEntry = { factory, component: DatePickerView };
