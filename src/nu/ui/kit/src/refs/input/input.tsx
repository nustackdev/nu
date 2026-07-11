// InputRef -- text input. Browser is source of truth.
//
// User types: local store updates immediately (controlled input).
// On blur or Enter: notify server. Server-initiated read: answer with current
// value. Server-initiated write: replace the value (canonical / reset).
// Class-level defaults (label, placeholder, value, type, max_length) seed the
// slice via mount props. Composes the kit Input primitive. Default face is
// display (Inter); code-shaped fields can opt into mono via a slice prop
// (`mono: true` on the seed) which flips `font-mono` at render time.

import { useId } from "react";
import { OP_NOTIFY } from "@nustackdev/ui-core";
import { Input } from "../../components/ui/input";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const factory: SliceFactory = (path, ctx, props) => ({
	type: "InputRef",
	value: typeof props?.value === "string" ? (props.value as string) : "",
	label: typeof props?.label === "string" ? (props.label as string) : "",
	placeholder: typeof props?.placeholder === "string" ? (props.placeholder as string) : "",
	inputType: typeof props?.type === "string" ? (props.type as string) : "text",
	maxLength: typeof props?.max_length === "number" ? (props.max_length as number) : null,
	mono: typeof props?.mono === "boolean" ? (props.mono as boolean) : false,
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			// Coerce: a null write (sentinel) must not make the input
			// uncontrolled. Always land a string.
			slice.value = v == null ? "" : String(v);
		}),
	get: () => {
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
	const mono = useStore((s) => Boolean(s.refs[path]?.mono));
	const setLocal = useStore((s) => s.setLocal);
	const send = useStore((s) => s.send);
	const id = useId();
	const commit = () => send({ op: OP_NOTIFY, ref: path, payload: null });
	return (
		<div className="flex flex-col gap-1">
			{label && (
				<label htmlFor={id} className="text-sm font-medium text-text-secondary">
					{label}
				</label>
			)}
			<Input
				id={id}
				type={inputType}
				placeholder={placeholder}
				maxLength={maxLength ?? undefined}
				value={value}
				className={mono ? "font-mono" : undefined}
				onChange={(e) => setLocal(path, e.target.value)}
				onBlur={commit}
				onKeyDown={(e) => {
					if (e.key === "Enter") {
						commit();
						(e.target as HTMLInputElement).blur();
					}
				}}
			/>
		</div>
	);
}

export const InputRef: RefEntry = { factory, component: InputView };
