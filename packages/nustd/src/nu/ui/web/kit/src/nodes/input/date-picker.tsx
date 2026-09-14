// DatePickerRef -- date input. Browser is source of truth.
//
// User picks a date: the node's `value` prop updates (local edit) and a notify
// fires. A server-initiated read is answered by the store from `value`. A
// server-initiated write replaces it, and needs a handler for the same reason
// InputRef does: a null write must land as "" so the field does not go
// uncontrolled and a following read answers "" rather than null.
//
// The value is an ISO `YYYY-MM-DD` string on the wire, both ways. The slot
// declares the starting date as `default`, so `value` reads with `default` as
// its fallback until a write or a pick lands one. Composes the kit DatePicker
// primitive (Popover + react-day-picker) so the calendar is consistent
// cross-browser and reads through kit tokens.

import { OPS } from "@nustackdev/ui-core";
import { DatePicker } from "../../components/ui/date-picker";
import { Text } from "../../components/ui/text";
import { type NodeEntry, type NodeProps, useSend, useSetValue, useStringProp } from "../../tree";

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

function DatePickerView({ path }: NodeProps) {
	const initial = useStringProp(path, "default");
	const value = useStringProp(path, "value", initial);
	const label = useStringProp(path, "label");
	const placeholder = useStringProp(path, "placeholder");
	const min = useStringProp(path, "min");
	const max = useStringProp(path, "max");
	const setValue = useSetValue(path);
	const send = useSend(path);
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
					setValue(toIso(next));
					send(OPS.notify);
				}}
			/>
		</div>
	);
}

export const DatePickerRef: NodeEntry = {
	component: DatePickerView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				props.value = payload == null ? "" : String(payload);
			}),
	},
};
