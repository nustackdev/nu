import * as React from "react";

import { cn } from "../../lib/utils";
import { Checkbox } from "./checkbox";
import { Label } from "./field";

// Multi choice as a list of checkboxes, one per option. The value is the
// list of ticked option values, kept in option order. Each box is a real
// kit Checkbox with its own label (Tab moves box to box, Space ticks, per
// a11y.md §3 Checkbox); the list is a `<fieldset>` (a group) named by
// whoever draws its label (`aria-labelledby`). Invalid, readonly and size
// reach every box, disabled reaches them through the fieldset.

export type ChoiceOption = { value: string; label: string };

/**
 * `list` with `item` ticked on or off, in the order `options` gives. Values
 * the options do not name stay, after the known ones, so a value that lands
 * before its options is not lost.
 */
export function toggleOption(
	list: readonly string[],
	item: string,
	on: boolean,
	options: readonly ChoiceOption[],
): string[] {
	const picked = new Set(list);
	if (on) picked.add(item);
	else picked.delete(item);
	const known = new Set(options.map((o) => o.value));
	return [
		...options.filter((o) => picked.has(o.value)).map((o) => o.value),
		...list.filter((v) => !known.has(v) && picked.has(v)),
	];
}

export interface CheckboxGroupProps
	extends Omit<React.ComponentProps<"fieldset">, "onChange" | "defaultValue"> {
	options: ChoiceOption[];
	value: string[];
	onValueChange: (value: string[]) => void;
	orientation?: "vertical" | "horizontal";
	size?: "sm" | "md" | "lg";
	invalid?: boolean;
	disabled?: boolean;
	/** Keep the look, take no ticks. */
	readOnly?: boolean;
	/** Focus the first box on mount. */
	autoFocus?: boolean;
}

export function CheckboxGroup({
	options,
	value,
	onValueChange,
	orientation = "vertical",
	size = "md",
	invalid,
	disabled,
	readOnly,
	autoFocus,
	id,
	className,
	...props
}: CheckboxGroupProps) {
	const auto = React.useId();
	const prefix = `${id ?? auto}-opt`;
	return (
		<fieldset
			data-slot="checkbox-group"
			id={id}
			disabled={disabled}
			className={cn(
				"m-0 min-w-0 border-0 p-0",
				orientation === "horizontal" ? "flex flex-row flex-wrap gap-4" : "flex flex-col gap-2",
				className,
			)}
			{...props}
		>
			{options.map((o, i) => {
				const boxId = `${prefix}-${i}`;
				return (
					<div key={o.value} className="flex items-center gap-2">
						<Checkbox
							id={boxId}
							value={o.value}
							size={size}
							invalid={invalid}
							disabled={disabled}
							autoFocus={autoFocus && i === 0}
							aria-readonly={readOnly || undefined}
							checked={value.includes(o.value)}
							onCheckedChange={(next) => {
								if (readOnly) return;
								onValueChange(toggleOption(value, o.value, next === true, options));
							}}
						/>
						<Label htmlFor={boxId} inline disabled={disabled}>
							{o.label}
						</Label>
					</div>
				);
			})}
		</fieldset>
	);
}
