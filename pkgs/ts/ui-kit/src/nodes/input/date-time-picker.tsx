// DateTimePickerRef -- date and time of day in one value. Browser is source
// of truth.
//
// The value is a local ISO "YYYY-MM-DDTHH:MM" on the node's `value` (null
// for none), both ways on the wire. A calendar pick lands the date (keeping the
// time there, or midnight) and sends `{event: "change"}` at once; the time
// field is text-like: typing is a local edit, blur commits. Enter on the
// closed date trigger or in the time field commits, then submits and asks an
// enclosing Form to submit. The clear button empties both parts and sends its
// change. `min` and `max` are ISO date-times: days outside are disabled, and
// on the first or last day the time field takes the bound. A write replaces
// the value (nil and "" land as null), a map write merges chrome, and `reset` puts
// the declared value back. See ./control.ts for the contract.
//
// Composes the kit DateTimePicker (DatePicker + TimePicker on one row). The
// label names both parts: the date trigger takes the id, the time field
// is named by the label and its own "Time".

import { type KeyboardEvent, useId } from "react";
import { Label } from "../../components/ui/field";
import { DateTimePicker } from "../../components/ui/time-picker";
import { type NodeEntry, type NodeProps, useBoolProp, useStringProp } from "../../tree";
import { asTextOrNull, isEnter, resetHandler, useCommit, useControl, valueWrite } from "./control";

const DATE_TIME = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?)?/;

/** A local ISO date-time ("YYYY-MM-DDTHH:MM[:SS]", or a bare date) as a Date, or null. */
export function fromIsoDateTime(s: string): Date | null {
	const m = DATE_TIME.exec(s);
	if (!m) return null;
	const [y, mo, d, h, mi, sec] = m.slice(1).map((x) => (x ? Number(x) : 0));
	if (!y || !mo || !d) return null;
	return new Date(y, mo - 1, d, h, mi, sec);
}

const pad = (n: number) => String(n).padStart(2, "0");

/** A Date as a local ISO "YYYY-MM-DDTHH:MM" ("" for none). */
export function toIsoDateTime(d: Date | null): string {
	if (!d) return "";
	const day = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
	return `${day}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function DateTimePickerView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	const min = useStringProp(path, "min");
	const max = useStringProp(path, "max");
	const clearable = useBoolProp(path, "clearable", true);
	const c = useControl(path);
	const { edit, commit, pick, submit } = useCommit(path);
	const ownLabel = useId();
	const timeId = useId();
	const labelId = c.label ? ownLabel : c.labelledBy;
	const onEnter = (e: KeyboardEvent<HTMLElement>) => {
		if (!isEnter(e)) return;
		e.preventDefault();
		submit(e.currentTarget);
	};
	return (
		<div className="flex flex-col gap-1">
			{c.label && (
				<Label id={ownLabel} htmlFor={c.id} required={c.required} disabled={c.disabled}>
					{c.label}
				</Label>
			)}
			<DateTimePicker
				id={c.id}
				value={fromIsoDateTime(value)}
				min={fromIsoDateTime(min) ?? undefined}
				max={fromIsoDateTime(max) ?? undefined}
				size={c.size}
				invalid={c.invalid}
				disabled={c.disabled}
				readOnly={c.readOnly}
				placeholder={c.placeholder || undefined}
				clearable={clearable && !c.readOnly}
				triggerProps={{
					autoFocus: c.autoFocus,
					"aria-labelledby": labelId ? `${labelId} ${c.id}` : undefined,
					"aria-describedby": c.describedBy,
					"aria-required": c.required || undefined,
					onKeyDown: onEnter,
				}}
				timeProps={{
					id: timeId,
					"aria-labelledby": labelId ? `${labelId} ${timeId}` : undefined,
					"aria-describedby": c.describedBy,
					"aria-invalid": c.invalid || undefined,
					required: c.required,
					onBlur: commit,
					onKeyDown: onEnter,
				}}
				onValueChange={(next) => edit(next ? toIsoDateTime(next) : null)}
				onValueCommit={(next) => pick(next ? toIsoDateTime(next) : null)}
			/>
		</div>
	);
}

export const DateTimePickerRef: NodeEntry = {
	component: DateTimePickerView,
	fill: true,
	input: { empty: null },
	handlers: {
		write: valueWrite(asTextOrNull),
		reset: resetHandler,
	},
};
