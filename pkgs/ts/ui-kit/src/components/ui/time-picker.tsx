import { Clock, X } from "lucide-react";
import * as React from "react";

import { useTouch } from "../../lib/touch";
import { cn } from "../../lib/utils";
import {
	BottomSheet,
	BottomSheetContent,
	BottomSheetFooter,
	BottomSheetItem,
} from "./bottom-sheet";
import { Button } from "./button";
import { DatePicker, type DatePickerProps } from "./date-picker";
import { IconButton } from "./icon-button";
import { Input } from "./input";

// TimePicker = the kit Input over a native `<input type="time">`. The browser
// owns the segments (hour, minute, optional second, AM/PM by locale), the
// arrow keys and min/max/step validity, so the value is always a valid
// "HH:MM" or "HH:MM:SS" string, or "" while a segment is empty. The native
// picker glyph is hidden for the lucide clock, so the field reads like the
// DatePicker trigger beside it; a clear button takes the clock's place while
// there is a value and the field is clearable.
//
// In touch mode (../../lib/touch.ts) the field is the same kit Input, read
// only, and a tap opens a time sheet (./bottom-sheet.tsx), the DatePicker's
// pattern: hour and minute columns (seconds too when the step or the value
// has them) of 44px sheet rows, 24h, the current value picked and scrolled
// into view, a Done button under them since a pick does not close it. Each
// pick moves the value (`onValueChange`), always a whole time; shutting the
// sheet on a moved value is the finished change (`onValueCommit`). `min`,
// `max` and `step` (seconds) shape the rows as they shape the native field.
//
// DateTimePicker = DatePicker + TimePicker on one row, one Date value. A
// calendar pick and a clear are finished changes (`onValueCommit`); typing in
// the time field only moves the value (`onValueChange`), the caller commits
// on blur.

type Size = "sm" | "md" | "lg";

/** "HH:MM" or "HH:MM:SS", or null. */
const TIME = /^(\d{2}):(\d{2})(?::(\d{2}))?$/;

/** Parse "HH:MM[:SS]" into [h, m, s], or null when it is not a time. */
function parseTime(raw: string): [number, number, number] | null {
	const m = TIME.exec(raw);
	if (!m) return null;
	const h = Number(m[1]);
	const min = Number(m[2]);
	const sec = m[3] ? Number(m[3]) : 0;
	if (h > 23 || min > 59 || sec > 59) return null;
	return [h, min, sec];
}

const pad = (n: number) => String(n).padStart(2, "0");

/** A Date's time of day as "HH:MM", or "HH:MM:SS" when it has seconds. */
function timeOf(d: Date): string {
	const hm = `${pad(d.getHours())}:${pad(d.getMinutes())}`;
	return d.getSeconds() ? `${hm}:${pad(d.getSeconds())}` : hm;
}

const glyphSizes = {
	sm: "right-1.5 [&_svg]:size-3",
	md: "right-2.5 [&_svg]:size-3.5",
	lg: "right-3 [&_svg]:size-4",
} as const;

export interface TimePickerProps
	extends Omit<
		React.ComponentProps<"input">,
		"size" | "type" | "value" | "defaultValue" | "onChange"
	> {
	/** "HH:MM", "HH:MM:SS" with a step under a minute, or "" for none. */
	value?: string;
	defaultValue?: string;
	/** Every move of the value, typing included. */
	onValueChange?: (value: string) => void;
	/** A finished change: the clear button. */
	onValueCommit?: (value: string) => void;
	size?: Size;
	invalid?: boolean;
	/** A clear button in the field while there is a value. */
	clearable?: boolean;
	/** The clear button's accessible name. */
	clearLabel?: string;
	/** Classes for the wrapper; `className` goes on the input. */
	wrapperClassName?: string;
}

export function TimePicker({
	value: valueProp,
	defaultValue = "",
	onValueChange,
	onValueCommit,
	size = "md",
	invalid,
	clearable = false,
	clearLabel = "Clear time",
	disabled,
	readOnly,
	className,
	wrapperClassName,
	...props
}: TimePickerProps) {
	const [internal, setInternal] = React.useState(defaultValue);
	const value = valueProp === undefined ? internal : valueProp;
	const input = React.useRef<HTMLInputElement>(null);

	const setValue = (next: string) => {
		if (valueProp === undefined) setInternal(next);
		onValueChange?.(next);
	};

	const clearing = clearable && value !== "" && !disabled && !readOnly;
	const touch = useTouch();

	const glyph = clearing ? (
		<IconButton
			variant="ghost"
			size={size === "lg" ? "sm" : "xs"}
			aria-label={clearLabel}
			className={cn("absolute top-1/2 -translate-y-1/2", size === "sm" ? "right-0.5" : "right-1.5")}
			onClick={() => {
				setValue("");
				onValueCommit?.("");
				input.current?.focus();
			}}
		>
			<X aria-hidden />
		</IconButton>
	) : (
		<span
			aria-hidden
			className={cn(
				"pointer-events-none absolute top-1/2 -translate-y-1/2 text-text-primary opacity-60",
				disabled && "opacity-30",
				glyphSizes[size],
			)}
		>
			<Clock />
		</span>
	);

	if (touch) {
		return (
			<TouchTimePicker
				{...props}
				inputRef={input}
				value={value}
				setValue={setValue}
				onValueCommit={onValueCommit}
				size={size}
				invalid={invalid}
				disabled={disabled}
				readOnly={readOnly}
				className={className}
				wrapperClassName={wrapperClassName}
				glyph={glyph}
			/>
		);
	}

	return (
		<div data-slot="time-picker" className={cn("relative w-full", wrapperClassName)}>
			<Input
				ref={input}
				type="time"
				size={size}
				invalid={invalid}
				disabled={disabled}
				readOnly={readOnly}
				value={value}
				onChange={(e) => setValue(e.target.value)}
				data-empty={value === "" || undefined}
				className={cn(
					"tabular-nums data-empty:text-text-muted",
					size === "sm" ? "pr-6" : "pr-8",
					// The lucide clock stands in for the native picker glyph.
					"[&::-webkit-calendar-picker-indicator]:hidden",
					"[&::-webkit-datetime-edit]:p-0",
					className,
				)}
				{...props}
			/>
			{glyph}
		</div>
	);
}

// ---- touch mode -------------------------------------------------------------

/** Seconds since midnight. */
const secondsOf = ([h, m, s]: [number, number, number]) => h * 3600 + m * 60 + s;

/** Seconds since midnight back to [h, m, s]. */
const partsOf = (t: number): [number, number, number] => [
	Math.floor(t / 3600),
	Math.floor(t / 60) % 60,
	t % 60,
];

/** `from` to `to` by `by`, with `keep` in it when it is a number. */
function steps(to: number, by: number, keep: number | undefined): number[] {
	const out: number[] = [];
	for (let n = 0; n <= to; n += by) out.push(n);
	if (keep !== undefined && !out.includes(keep)) out.push(keep);
	return out.sort((a, b) => a - b);
}

interface TouchTimePickerProps
	extends Omit<
		React.ComponentProps<"input">,
		"size" | "type" | "value" | "defaultValue" | "onChange"
	> {
	inputRef: React.RefObject<HTMLInputElement | null>;
	value: string;
	setValue: (next: string) => void;
	onValueCommit?: (value: string) => void;
	size: Size;
	invalid?: boolean;
	wrapperClassName?: string;
	/** The clock, or the clear button. */
	glyph: React.ReactNode;
}

function TouchTimePicker({
	inputRef,
	value,
	setValue,
	onValueCommit,
	size,
	invalid,
	disabled,
	readOnly,
	min,
	max,
	step,
	placeholder = "--:--",
	className,
	wrapperClassName,
	glyph,
	onClick,
	onKeyDown,
	...props
}: TouchTimePickerProps) {
	const [open, setOpenState] = React.useState(false);
	// The value when the sheet opened: shutting it on another one commits.
	const opened = React.useRef(value);
	const setOpen = (next: boolean) => {
		if (next === open) return;
		if (next) opened.current = value;
		else if (value !== opened.current) onValueCommit?.(value);
		setOpenState(next);
	};
	const openSheet = () => {
		if (!disabled && !readOnly) setOpen(true);
	};

	const stepNum = Number(step);
	const stepSec = Number.isFinite(stepNum) && stepNum > 0 ? Math.round(stepNum) : 60;
	const parts = parseTime(value);
	const withSeconds = /:\d{2}:\d{2}$/.test(value) || stepSec % 60 !== 0;
	const lo = parseTime(String(min ?? ""));
	const hi = parseTime(String(max ?? ""));
	const loSec = lo ? secondsOf(lo) : 0;
	const hiSec = hi ? secondsOf(hi) : 86399;

	// A pick in one column keeps the others, from the value, or the earliest allowed time.
	const base = parts ?? lo ?? [0, 0, 0];
	const pick = (at: 0 | 1 | 2, n: number) => {
		const next = [...base] as [number, number, number];
		next[at] = n;
		if (!withSeconds) next[2] = 0;
		const [h, m, s] = partsOf(Math.min(hiSec, Math.max(loSec, secondsOf(next))));
		const hm = `${pad(h)}:${pad(m)}`;
		setValue(withSeconds ? `${hm}:${pad(s)}` : hm);
	};

	const minuteBy = stepSec >= 60 && stepSec < 3600 && stepSec % 60 === 0 ? stepSec / 60 : 1;
	const secondBy = stepSec < 60 ? stepSec : 1;
	const [h, m] = base;
	const columns = [
		{
			label: "Hour",
			at: 0 as const,
			rows: steps(23, 1, parts?.[0]),
			off: (n: number) => n * 3600 + 3599 < loSec || n * 3600 > hiSec,
		},
		{
			label: "Minute",
			at: 1 as const,
			rows: steps(59, minuteBy, parts?.[1]),
			off: (n: number) => h * 3600 + n * 60 + 59 < loSec || h * 3600 + n * 60 > hiSec,
		},
		...(withSeconds
			? [
					{
						label: "Second",
						at: 2 as const,
						rows: steps(59, secondBy, parts?.[2]),
						off: (n: number) => {
							const t = h * 3600 + m * 60 + n;
							return t < loSec || t > hiSec;
						},
					},
				]
			: []),
	];

	return (
		<div data-slot="time-picker" className={cn("relative w-full", wrapperClassName)}>
			<Input
				{...props}
				ref={inputRef}
				type="text"
				readOnly
				inputMode="none"
				size={size}
				invalid={invalid}
				disabled={disabled}
				aria-readonly={readOnly || undefined}
				aria-haspopup="dialog"
				aria-expanded={open}
				placeholder={placeholder}
				value={value}
				data-empty={value === "" || undefined}
				className={cn(
					"tabular-nums data-empty:text-text-muted",
					size === "sm" ? "pr-6" : "pr-8",
					className,
				)}
				onClick={(e) => {
					onClick?.(e);
					if (!e.defaultPrevented) openSheet();
				}}
				onKeyDown={(e) => {
					onKeyDown?.(e);
					if (e.defaultPrevented) return;
					if (e.key !== "Enter" && e.key !== " " && e.key !== "ArrowDown") return;
					e.preventDefault();
					openSheet();
				}}
			/>
			{glyph}
			<BottomSheet open={open} onOpenChange={setOpen}>
				<BottomSheetContent label={props["aria-label"] ?? "Pick a time"}>
					<div data-slot="time-picker-content" className="flex flex-col">
						<div className="flex gap-2">
							{columns.map((c) => (
								<TimeColumn
									key={c.label}
									label={c.label}
									rows={c.rows}
									selected={parts?.[c.at]}
									off={c.off}
									onPick={(n) => pick(c.at, n)}
								/>
							))}
						</div>
						<BottomSheetFooter>
							<Button size="lg" onClick={() => setOpen(false)}>
								Done
							</Button>
						</BottomSheetFooter>
					</div>
				</BottomSheetContent>
			</BottomSheet>
		</div>
	);
}

// One column of the time sheet: a label over a scrolling list of rows, the
// picked one centred when the sheet opens.
function TimeColumn({
	label,
	rows,
	selected,
	off,
	onPick,
}: {
	label: string;
	rows: number[];
	selected: number | undefined;
	off: (n: number) => boolean;
	onPick: (n: number) => void;
}) {
	const list = React.useRef<HTMLDivElement>(null);
	React.useLayoutEffect(() => {
		const box = list.current;
		const row = box?.querySelector<HTMLElement>("[aria-selected=true]");
		if (!box || !row) return;
		box.scrollTop = row.offsetTop - (box.clientHeight - row.offsetHeight) / 2;
	}, []);
	return (
		<div className="flex min-w-0 flex-1 flex-col">
			<div className="pb-1 text-center text-xs uppercase tracking-wider text-text-muted">
				{label}
			</div>
			<div
				ref={list}
				role="listbox"
				aria-label={label}
				data-slot="time-picker-column"
				className="relative h-64 overflow-y-auto overscroll-contain"
			>
				{rows.map((n) => {
					const on = n === selected;
					return (
						<BottomSheetItem
							key={n}
							role="option"
							aria-selected={on}
							selected={on}
							disabled={off(n)}
							className={cn(
								"justify-center tabular-nums",
								on && "rounded-sm bg-accent text-accent-fg active:bg-accent-pressed",
							)}
							onClick={() => onPick(n)}
						>
							{pad(n)}
						</BottomSheetItem>
					);
				})}
			</div>
		</div>
	);
}

export interface DateTimePickerProps
	extends Pick<
		DatePickerProps,
		"variant" | "size" | "invalid" | "disabled" | "placeholder" | "format" | "id" | "name"
	> {
	value?: Date | null;
	defaultValue?: Date | null;
	/** Every move of the value, typing in the time field included. */
	onValueChange?: (value: Date | null) => void;
	/** A finished change: a calendar pick or a clear. */
	onValueCommit?: (value: Date | null) => void;
	min?: Date;
	max?: Date;
	/** The time field takes no typing; the calendar stays shut. */
	readOnly?: boolean;
	/** A clear button on the date part while there is a value; it clears both. */
	clearable?: boolean;
	clearLabel?: string;
	className?: string;
	"aria-label"?: string;
	/** More props for the date trigger button (aria, a key handler, autofocus). */
	triggerProps?: React.ComponentProps<"button">;
	/** More props for the time input (aria, blur and key handlers). */
	timeProps?: Omit<TimePickerProps, "value" | "defaultValue" | "onValueChange" | "size">;
}

/** Midnight-free day compare: the same calendar day. */
function sameDay(a: Date, b: Date): boolean {
	return (
		a.getFullYear() === b.getFullYear() &&
		a.getMonth() === b.getMonth() &&
		a.getDate() === b.getDate()
	);
}

function withTime(day: Date, time: string): Date {
	const [h, m, s] = parseTime(time) ?? [0, 0, 0];
	return new Date(day.getFullYear(), day.getMonth(), day.getDate(), h, m, s);
}

export function DateTimePicker({
	value: valueProp,
	defaultValue = null,
	onValueChange,
	onValueCommit,
	variant,
	size = "md",
	invalid,
	disabled,
	readOnly,
	placeholder = "Pick a date",
	format,
	min,
	max,
	id,
	name,
	clearable = false,
	clearLabel = "Clear date and time",
	className,
	"aria-label": ariaLabel,
	triggerProps,
	timeProps,
}: DateTimePickerProps) {
	const [internal, setInternal] = React.useState<Date | null>(defaultValue);
	const value = valueProp === undefined ? internal : valueProp;

	// The time field's draft: a time typed before any date, or an emptied
	// field, stays here; the value moves only with a date and a whole time.
	const shown = value ? timeOf(value) : "";
	const [time, setTime] = React.useState(shown);
	React.useEffect(() => {
		setTime(shown);
	}, [shown]);

	const setValue = (next: Date | null, commit: boolean) => {
		if (valueProp === undefined) setInternal(next);
		onValueChange?.(next);
		if (commit) onValueCommit?.(next);
	};

	// With no time yet, a pick on the first allowed day starts at the earliest allowed time.
	const firstTime = (d: Date) => (min && sameDay(d, min) ? timeOf(min) : "");

	return (
		// A fluid row: the time drops under the date when the row cannot hold
		// a readable date beside it, rather than squeezing the date to nothing.
		<div
			data-slot="date-time-picker"
			className={cn("flex w-full flex-wrap items-center gap-2", className)}
		>
			<div className="min-w-32 flex-[1_1_9rem]">
				<DatePicker
					id={id}
					name={name}
					variant={variant}
					size={size}
					invalid={invalid}
					disabled={disabled || readOnly}
					placeholder={placeholder}
					format={format}
					min={min}
					max={max}
					aria-label={ariaLabel}
					clearable={clearable}
					clearLabel={clearLabel}
					triggerProps={triggerProps}
					value={value}
					onValueChange={(next) => {
						if (!next) {
							setTime("");
							setValue(null, true);
							return;
						}
						// A pick keeps the time already there, or the draft, or midnight.
						setValue(withTime(next, time || (value ? timeOf(value) : "") || firstTime(next)), true);
					}}
				/>
			</div>
			<TimePicker
				aria-label="Time"
				{...timeProps}
				wrapperClassName={cn("w-32 shrink-0", timeProps?.wrapperClassName)}
				size={size}
				invalid={invalid}
				disabled={disabled}
				readOnly={readOnly}
				min={value && min && sameDay(value, min) ? timeOf(min) : timeProps?.min}
				max={value && max && sameDay(value, max) ? timeOf(max) : timeProps?.max}
				value={time}
				onValueChange={(next) => {
					setTime(next);
					if (value && parseTime(next)) setValue(withTime(value, next), false);
				}}
				onValueCommit={(next) => {
					// The touch sheet shutting on a new time: a finished change.
					if (value && parseTime(next)) setValue(withTime(value, next), true);
					timeProps?.onValueCommit?.(next);
				}}
				onBlur={(e) => {
					// An emptied field goes back to the value's time once you leave it.
					setTime(shown);
					timeProps?.onBlur?.(e);
				}}
			/>
		</div>
	);
}
