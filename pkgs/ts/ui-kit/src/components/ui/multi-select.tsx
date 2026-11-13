import { Command as CommandPrimitive } from "cmdk";
import { Check } from "lucide-react";
import * as React from "react";

import { cn } from "../../lib/utils";
import { type ChoiceOption, toggleOption } from "./checkbox-group";
import {
	Combobox,
	ComboboxContent,
	ComboboxEmpty,
	ComboboxInput,
	ComboboxList,
	ComboboxTrigger,
	comboboxItemClass,
} from "./combobox";

// Dropdown multi choice with a search field: the kit Combobox (Popover +
// cmdk) where a pick ticks the option on or off and the list stays open, so
// several picks take one trip. The value is the list of picked option
// values, in option order. The trigger is the real control
// (`role="combobox"`): the rest props (id, aria) land on it. It shows the
// first picks as chips and a count for the rest. In the list each option
// carries `aria-checked`, the listbox is `aria-multiselectable`.

const chipSize = {
	sm: "h-4 px-1 text-xs",
	md: "h-5 px-1.5 text-xs",
	lg: "h-6 px-2 text-sm",
} as const;

export interface MultiSelectProps
	extends Omit<React.ComponentProps<"button">, "value" | "defaultValue" | "onChange"> {
	options: ChoiceOption[];
	value: string[];
	onValueChange: (value: string[]) => void;
	placeholder?: string;
	/** The search field's placeholder. */
	searchPlaceholder?: string;
	/** What the list says when nothing matches the search. */
	emptyText?: string;
	/** How many picks show as chips before the rest fold into a count. */
	maxChips?: number;
	size?: "sm" | "md" | "lg";
	invalid?: boolean;
}

export function MultiSelect({
	options,
	value,
	onValueChange,
	placeholder = "",
	searchPlaceholder = "Search",
	emptyText = "No match",
	maxChips = 2,
	size = "md",
	invalid,
	disabled,
	className,
	...props
}: MultiSelectProps) {
	const [open, setOpen] = React.useState(false);
	const labels = new Map(options.map((o) => [o.value, o.label]));
	const shown = value.slice(0, maxChips);
	const more = value.length - shown.length;
	return (
		<Combobox open={open} onOpenChange={setOpen}>
			<ComboboxTrigger
				size={size}
				invalid={invalid}
				disabled={disabled}
				data-slot="multi-select-trigger"
				data-placeholder={value.length ? undefined : ""}
				className={className}
				{...props}
			>
				<span className="flex min-w-0 items-center gap-1">
					{value.length === 0
						? placeholder
						: shown.map((v) => (
								<span
									key={v}
									data-slot="multi-select-chip"
									className={cn(
										"inline-flex max-w-32 shrink-0 items-center rounded-sm border border-transparent bg-bg-press font-medium text-text-primary",
										chipSize[size],
									)}
								>
									<span className="truncate">{labels.get(v) ?? v}</span>
								</span>
							))}
					{more > 0 ? <span className="shrink-0 text-sm text-text-secondary">+{more}</span> : null}
				</span>
			</ComboboxTrigger>
			<ComboboxContent>
				<ComboboxInput placeholder={searchPlaceholder} />
				<ComboboxList aria-multiselectable="true">
					<ComboboxEmpty>{emptyText}</ComboboxEmpty>
					{options.map((o) => {
						const on = value.includes(o.value);
						return (
							// cmdk filters on value plus keywords, so the label rides as a
							// keyword and typing either one finds the option.
							<CommandPrimitive.Item
								key={o.value}
								value={o.value}
								keywords={[o.label]}
								data-slot="multi-select-item"
								aria-checked={on}
								onSelect={() => onValueChange(toggleOption(value, o.value, !on, options))}
								className={comboboxItemClass}
							>
								{o.label}
								{on && <Check className="ml-auto size-4 text-accent-text" />}
							</CommandPrimitive.Item>
						);
					})}
				</ComboboxList>
			</ComboboxContent>
		</Combobox>
	);
}
