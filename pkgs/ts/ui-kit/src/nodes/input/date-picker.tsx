// DatePickerRef -- date input. Browser is source of truth.
//
// The value is an ISO `YYYY-MM-DD` string on the node's `value` ("" for
// none), both ways on the wire. A pick lands it and sends `{event: "change"}`
// at once (./control.ts). Enter on the closed trigger submits (and asks an
// enclosing Form to submit); Space and ArrowDown open the calendar. A write
// replaces the value (nil lands as "" so the field never goes uncontrolled),
// a map write merges chrome, and `reset` puts the declared value back.
//
// Composes the kit DatePicker primitive (Popover + react-day-picker), so the
// calendar is consistent cross-browser and reads through kit tokens. The
// trigger is the control: it takes the id, the label and the Field's aria.

import { useId } from "react";
import { DatePicker } from "../../components/ui/date-picker";
import { Text } from "../../components/ui/text";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";
import { asText, isEnter, resetHandler, useCommit, useControl, valueWrite } from "./control";

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
	const value = useStringProp(path, "value");
	const min = useStringProp(path, "min");
	const max = useStringProp(path, "max");
	const c = useControl(path);
	const { pick, submit } = useCommit(path);
	const labelId = useId();
	return (
		<div className="flex flex-col gap-1">
			{c.label && (
				<Text
					as="span"
					id={labelId}
					size="sm"
					tone="secondary"
					weight="medium"
					className={c.disabled ? "opacity-50" : undefined}
				>
					{c.label}
				</Text>
			)}
			<DatePicker
				id={c.id}
				value={fromIso(value)}
				min={fromIso(min) ?? undefined}
				max={fromIso(max) ?? undefined}
				size={c.size}
				invalid={c.invalid}
				disabled={c.disabled || c.readOnly}
				placeholder={c.placeholder || undefined}
				triggerProps={{
					autoFocus: c.autoFocus,
					"aria-labelledby": c.label ? `${labelId} ${c.id}` : c.labelledBy,
					"aria-describedby": c.describedBy,
					"aria-required": c.required || undefined,
					onKeyDown: (e) => {
						if (!isEnter(e)) return;
						e.preventDefault();
						submit(e.currentTarget);
					},
				}}
				onValueChange={(next) => pick(toIso(next))}
			/>
		</div>
	);
}

export const DatePickerRef: NodeEntry = {
	component: DatePickerView,
	fill: true,
	input: { empty: "" },
	handlers: {
		write: valueWrite(asText),
		reset: resetHandler,
	},
};
