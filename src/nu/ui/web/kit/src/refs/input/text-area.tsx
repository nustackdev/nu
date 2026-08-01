// TextAreaRef -- multi-line text input. Browser is source of truth.
//
// User types: local store updates immediately (controlled).
// Commit moments (blur, cmd/ctrl-enter): notify server.
// Server-initiated read: answer with current local value.
// Server-initiated write: replace the value (canonical / reset).
// Class-level defaults (placeholder, rows, max_length, auto_resize) seed
// the slice via mount props. Composes the kit TextArea primitive; the
// primitive owns autoResize via CSS `field-sizing: content`. Default face
// is display (Inter); code-shaped fields can opt into mono via a slice
// prop (`mono: true` on the seed).

import { useId } from "react";
import { OP_NOTIFY } from "@nustackdev/ui-core";
import { TextArea } from "../../components/ui/text-area";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const factory: SliceFactory = (path, ctx, props) => ({
	type: "TextAreaRef",
	value: typeof props?.value === "string" ? (props.value as string) : "",
	label: typeof props?.label === "string" ? (props.label as string) : "",
	placeholder: typeof props?.placeholder === "string" ? (props.placeholder as string) : "",
	rows: typeof props?.rows === "number" ? (props.rows as number) : 4,
	max_length: typeof props?.max_length === "number" ? (props.max_length as number) : null,
	auto_resize: typeof props?.auto_resize === "boolean" ? (props.auto_resize as boolean) : false,
	mono: typeof props?.mono === "boolean" ? (props.mono as boolean) : false,
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

function TextAreaView({ path }: { path: string }) {
	const value = useStore((s) => (s.refs[path]?.value as string) ?? "");
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const placeholder = useStore((s) => (s.refs[path]?.placeholder as string) ?? "");
	const rows = useStore((s) => (s.refs[path]?.rows as number) ?? 4);
	const maxLength = useStore((s) => s.refs[path]?.max_length as number | null);
	const autoResize = useStore((s) => Boolean(s.refs[path]?.auto_resize));
	const mono = useStore((s) => Boolean(s.refs[path]?.mono));
	const setLocal = useStore((s) => s.setLocal);
	const send = useStore((s) => s.send);
	const id = useId();

	const commit = () => send({ op: OP_NOTIFY, ref: path, payload: null });
	const cls = [autoResize ? "[field-sizing:content]" : null, mono ? "font-mono" : null]
		.filter(Boolean)
		.join(" ");

	return (
		<div className="flex flex-col gap-1">
			{label && (
				<label htmlFor={id} className="text-sm font-medium text-text-secondary">
					{label}
				</label>
			)}
			<TextArea
				id={id}
				value={value}
				rows={rows}
				placeholder={placeholder}
				maxLength={maxLength ?? undefined}
				className={cls || undefined}
				onChange={(e) => setLocal(path, e.target.value)}
				onBlur={commit}
				onKeyDown={(e) => {
					if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
						commit();
						(e.target as HTMLTextAreaElement).blur();
					}
				}}
			/>
		</div>
	);
}

export const TextAreaRef: RefEntry = { factory, component: TextAreaView };
