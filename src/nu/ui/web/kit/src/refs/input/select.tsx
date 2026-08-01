// SelectRef -- single-select dropdown. Browser is source of truth.
//
// User picks: local store updates immediately, notify ships to server.
// Server write payload: a string overwrites `selected`; a map with an
// `options` key overwrites `options`. Server-initiated read: answer with
// the current selected value. Class-level defaults (options, selected,
// placeholder) seed the slice via mount props. Composes the kit Select
// primitive (Radix Select) so the popover reads through tokens on both
// themes; native <select> is dropped.

import { useId } from "react";
import { OP_NOTIFY } from "@nustackdev/ui-core";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "../../components/ui/select";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

type Option = { value: string; label: string };

function normalizeOptions(raw: unknown): Option[] {
	if (!Array.isArray(raw)) return [];
	const out: Option[] = [];
	for (const item of raw) {
		if (typeof item === "string") {
			out.push({ value: item, label: item });
		} else if (item && typeof item === "object") {
			const o = item as { value?: unknown; label?: unknown };
			const value = o.value == null ? "" : String(o.value);
			const label = o.label == null ? value : String(o.label);
			out.push({ value, label });
		}
	}
	return out;
}

const factory: SliceFactory = (path, ctx, props) => ({
	type: "SelectRef",
	value: null,
	selected: typeof props?.selected === "string" ? (props.selected as string) : "",
	label: typeof props?.label === "string" ? (props.label as string) : "",
	options: normalizeOptions(props?.options),
	placeholder: typeof props?.placeholder === "string" ? (props.placeholder as string) : "",
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			if (v && typeof v === "object" && !Array.isArray(v) && "options" in (v as object)) {
				const p = v as { options: unknown };
				slice.options = normalizeOptions(p.options);
				return;
			}
			// Bare value push (string or coercible). Nil clears the selection.
			slice.selected = v == null ? "" : String(v);
		}),
	get: () => {
		const slice = useStore.getState().refs[path];
		return (slice?.selected as string) ?? "";
	},
});

function SelectView({ path }: { path: string }) {
	const selected = useStore((s) => (s.refs[path]?.selected as string) ?? "");
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const options = useStore((s) => (s.refs[path]?.options as Option[]) ?? []);
	const placeholder = useStore((s) => (s.refs[path]?.placeholder as string) ?? "");
	const send = useStore((s) => s.send);
	const id = useId();
	return (
		<div className="flex flex-col gap-1">
			{label && (
				<label htmlFor={id} className="text-sm font-medium text-text-secondary">
					{label}
				</label>
			)}
			<Select
				value={selected || undefined}
				onValueChange={(next) => {
					useStore.setState((draft) => {
						const slice = draft.refs[path];
						if (slice) slice.selected = next;
					});
					send({ op: OP_NOTIFY, ref: path, payload: null });
				}}
			>
				<SelectTrigger id={id}>
					<SelectValue placeholder={placeholder} />
				</SelectTrigger>
				<SelectContent>
					{options.map((o) => (
						<SelectItem key={o.value} value={o.value}>
							{o.label}
						</SelectItem>
					))}
				</SelectContent>
			</Select>
		</div>
	);
}

export const SelectRef: RefEntry = { factory, component: SelectView };
