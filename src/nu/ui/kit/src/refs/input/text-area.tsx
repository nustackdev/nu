// TextAreaRef -- multi-line text input. Browser is source of truth.
//
// User types: local store updates immediately (controlled).
// Commit moments (blur, cmd/ctrl-enter): notify server.
// Server-initiated read: answer with current local value.
// Server-initiated write: replace the value (canonical / reset).
// Class-level defaults (placeholder, rows, max_length, auto_resize) seed
// the slice via mount props.

import { useEffect, useRef } from "react";
import { OP_NOTIFY } from "@nustackdev/ui-core";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const factory: SliceFactory = (path, ctx, props) => ({
	type: "TextAreaRef",
	value: typeof props?.value === "string" ? (props.value as string) : "",
	placeholder: typeof props?.placeholder === "string" ? (props.placeholder as string) : "",
	rows: typeof props?.rows === "number" ? (props.rows as number) : 4,
	max_length: typeof props?.max_length === "number" ? (props.max_length as number) : null,
	auto_resize: typeof props?.auto_resize === "boolean" ? (props.auto_resize as boolean) : false,
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			// Coerce: a null write (sentinel) must not make the textarea
			// uncontrolled. Always land a string.
			slice.value = v == null ? "" : String(v);
		}),
	get: () => {
		const slice = useStore.getState().refs[path];
		return (slice?.value as string) ?? "";
	},
});

function TextAreaView({ path }: { path: string }) {
	const value = useStore((s) => (s.refs[path]?.value as string) ?? "");
	const placeholder = useStore((s) => (s.refs[path]?.placeholder as string) ?? "");
	const rows = useStore((s) => (s.refs[path]?.rows as number) ?? 4);
	const maxLength = useStore((s) => s.refs[path]?.max_length as number | null);
	const autoResize = useStore((s) => Boolean(s.refs[path]?.auto_resize));
	const setLocal = useStore((s) => s.setLocal);
	const send = useStore((s) => s.send);
	const ref = useRef<HTMLTextAreaElement | null>(null);

	// biome-ignore lint/correctness/useExhaustiveDependencies: value drives the resize recompute
	useEffect(() => {
		if (!autoResize) return;
		const el = ref.current;
		if (!el) return;
		el.style.height = "auto";
		el.style.height = `${el.scrollHeight}px`;
	}, [value]);

	const commit = () => send({ op: OP_NOTIFY, ref: path, payload: null });

	return (
		<textarea
			ref={ref}
			className="w-full rounded border px-3 py-2 font-mono text-sm"
			value={value}
			rows={rows}
			placeholder={placeholder}
			maxLength={maxLength ?? undefined}
			onChange={(e) => setLocal(path, e.target.value)}
			onBlur={commit}
			onKeyDown={(e) => {
				if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
					commit();
					(e.target as HTMLTextAreaElement).blur();
				}
			}}
		/>
	);
}

export const TextAreaRef: RefEntry = { factory, component: TextAreaView };
