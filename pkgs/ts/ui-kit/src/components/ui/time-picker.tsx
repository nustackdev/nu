import { Clock, X } from "lucide-react";
import * as React from "react";

import { cn } from "../../lib/utils";
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
			{clearing ? (
				<IconButton
					variant="ghost"
					size={size === "lg" ? "sm" : "xs"}
					aria-label={clearLabel}
					className={cn(
						"absolute top-1/2 -translate-y-1/2",
						size === "sm" ? "right-0.5" : "right-1.5",
					)}
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
			)}
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
		<div data-slot="date-time-picker" className={cn("flex w-full items-center gap-2", className)}>
			<div className="min-w-0 flex-1">
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
				onBlur={(e) => {
					// An emptied field goes back to the value's time once you leave it.
					setTime(shown);
					timeProps?.onBlur?.(e);
				}}
			/>
		</div>
	);
}
