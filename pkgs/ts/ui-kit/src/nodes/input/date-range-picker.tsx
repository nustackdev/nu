// DateRangePickerRef -- a span of days. Browser is source of truth.
//
// The value is `{start, end}`, each an ISO "YYYY-MM-DD" ("" for none), on the
// node's `value`, both ways on the wire. Picks in the open calendar are local
// edits (the first click starts the range, the second ends it); closing the
// calendar commits them, a change when the range moved. Enter on the closed
// trigger commits, then submits and asks an enclosing Form to submit; Space
// and ArrowDown open the calendar. The clear button (and Backspace or Delete
// on the trigger) empties the range and sends its change at once. A write
// takes `{start, end}` bare or as `{value: {start, end}}`; nil lands as the
// empty range, any other map merges chrome, and `reset` puts the declared
// value back. See ./control.ts for the contract.
//
// Composes the kit DateRangePicker (Popover + react-day-picker, two months).
// The trigger is the control: it takes the id, the label and the Field's aria.

import type { NodeHandler } from "@nustackdev/ui-core";
import { useId, useRef } from "react";
import type { DateRange } from "react-day-picker";
import { DateRangePicker } from "../../components/ui/date-picker";
import { Text } from "../../components/ui/text";
import { type NodeEntry, type NodeProps, useBoolProp, useProp, useStringProp } from "../../tree";
import { isEnter, resetHandler, useCommit, useControl, valueWrite } from "./control";
import { fromIso, toIso } from "./date-picker";

export type IsoRange = { start: string; end: string };

const EMPTY: IsoRange = { start: "", end: "" };

function isRange(raw: unknown): raw is Partial<IsoRange> {
	return (
		Boolean(raw) &&
		typeof raw === "object" &&
		!Array.isArray(raw) &&
		("start" in (raw as object) || "end" in (raw as object))
	);
}

/** Any raw value as a range of ISO strings; anything else is the empty range. */
export function asRange(raw: unknown): IsoRange {
	if (!isRange(raw)) return { ...EMPTY };
	const text = (v: unknown) => (v == null ? "" : String(v));
	return { start: text(raw.start), end: text(raw.end) };
}

function toRange(v: IsoRange): DateRange | null {
	const from = fromIso(v.start);
	if (!from) return null;
	return { from, to: fromIso(v.end) ?? undefined };
}

function fromRange(r: DateRange | null): IsoRange {
	if (!r?.from) return { ...EMPTY };
	return { start: toIso(r.from), end: toIso(r.to ?? null) };
}

const sameRange = (a: IsoRange, b: IsoRange) => a.start === b.start && a.end === b.end;

const write = valueWrite(asRange);

/** A bare `{start, end}` is the value; any other map merges chrome. */
const rangeWrite: NodeHandler = (ctx, payload) =>
	write(ctx, isRange(payload) ? { value: payload } : payload);

function DateRangePickerView({ path }: NodeProps) {
	const raw = useProp<unknown>(path, "value", null);
	const value = asRange(raw);
	// The value as the calendar opened: picks that end where they began send nothing.
	const opened = useRef<unknown>(undefined);
	const min = useStringProp(path, "min");
	const max = useStringProp(path, "max");
	const clearable = useBoolProp(path, "clearable", true);
	const c = useControl(path);
	const { edit, commit, pick, submit } = useCommit(path);
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
			<DateRangePicker
				id={c.id}
				value={toRange(value)}
				min={fromIso(min) ?? undefined}
				max={fromIso(max) ?? undefined}
				size={c.size}
				invalid={c.invalid}
				disabled={c.disabled || c.readOnly}
				placeholder={c.placeholder || undefined}
				clearable={clearable}
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
				onValueChange={(next) => (next?.from ? edit(fromRange(next)) : pick({ ...EMPTY }))}
				onOpenChange={(open) => {
					if (open) {
						opened.current = raw;
						return;
					}
					const was = opened.current;
					opened.current = undefined;
					if (was !== undefined && sameRange(asRange(was), value)) edit(was);
					commit();
				}}
			/>
		</div>
	);
}

export const DateRangePickerRef: NodeEntry = {
	component: DateRangePickerView,
	fill: true,
	input: { empty: () => ({ ...EMPTY }) },
	handlers: {
		write: rangeWrite,
		reset: resetHandler,
	},
};
