// DatePickerRef -- date input. Browser is source of truth.
//
// User picks a date: local store updates and notify fires. Server-initiated
// read: answer with current ISO value. Server-initiated write: replace.
// Class-level defaults (label, placeholder, min, max, default) seed the
// slice via mount props; `default` seeds `value`. Composes the kit
// DatePicker primitive (Popover + react-day-picker) so the calendar is
// consistent cross-browser and reads through kit tokens.

import { OP_NOTIFY } from "@nustackdev/ui-core";
import { DatePicker } from "../../components/ui/date-picker";
import { Text } from "../../components/ui/text";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

function toIso(d: Date | null): string {
	if (!d) return "";
	const y = d.getFullYear();
	const m = String(d.getMonth() + 1).padStart(2, "0");
	const day = String(d.getDate()).padStart(2, "0");
	return `${y}-${m}-${day}`;
}

function fromIso(s: string): Date | null {
	if (!s) return null;
	// Interpret as local date to avoid off-by-one UTC shifts on formatting.
	const [y, m, d] = s.split("-").map(Number);
	if (!y || !m || !d) return null;
	return new Date(y, m - 1, d);
}

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
		<div className="flex flex-col gap-1">
			{label && (
				<Text as="span" size="sm" tone="secondary" weight="medium">
					{label}
				</Text>
			)}
			<DatePicker
				value={fromIso(value)}
				min={fromIso(min) ?? undefined}
				max={fromIso(max) ?? undefined}
				placeholder={placeholder || undefined}
				onValueChange={(next) => {
					setLocal(path, toIso(next));
					send({ op: OP_NOTIFY, ref: path, payload: null });
				}}
			/>
		</div>
	);
}

export const DatePickerRef: RefEntry = { factory, component: DatePickerView };
