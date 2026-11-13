import { Popover as PopoverPrimitive } from "radix-ui";
import * as React from "react";

import { cn } from "../../lib/utils";
import type { ChoiceOption } from "./checkbox-group";
import { comboboxItemClass } from "./combobox";
import { Input } from "./input";

// A text field with a suggestion list under it. Any text is a value; the
// suggestions are a shortcut. The field is the real control, an ARIA 1.2
// combobox (`aria-autocomplete="list"`, `aria-activedescendant`) whose list
// opens as you type. Arrow down/up move the highlight (down opens a closed
// list), Enter on a highlighted suggestion picks it, Escape closes. Nothing
// is highlighted until an arrow moves there, so Enter on plain typing is
// left to the caller (a submit). Focus never leaves the field: the list is
// a Popover anchored to it that does not take focus, and a click on a
// suggestion keeps the caret where it was. The list and its rows share the
// Combobox look.

export interface AutocompleteProps
	extends Omit<React.ComponentProps<"input">, "value" | "onChange" | "size" | "defaultValue"> {
	/** The text in the field. */
	value: string;
	/** Each keystroke. */
	onValueChange: (value: string) => void;
	/** A suggestion was picked: its value is the new text. */
	onPick: (value: string) => void;
	options: ChoiceOption[];
	size?: "sm" | "md" | "lg";
	invalid?: boolean;
}

function matching(options: ChoiceOption[], text: string): ChoiceOption[] {
	const q = text.trim().toLowerCase();
	if (!q) return options;
	return options.filter(
		(o) => o.label.toLowerCase().includes(q) || o.value.toLowerCase().includes(q),
	);
}

export function Autocomplete({
	value,
	onValueChange,
	onPick,
	options,
	size = "md",
	invalid,
	id,
	className,
	onKeyDown,
	onBlur,
	readOnly,
	disabled,
	...props
}: AutocompleteProps) {
	const auto = React.useId();
	const listId = `${id ?? auto}-list`;
	const [open, setOpen] = React.useState(false);
	const [active, setActive] = React.useState(-1);
	const anchor = React.useRef<HTMLDivElement>(null);
	const matches = React.useMemo(() => matching(options, value), [options, value]);
	const shown = open && matches.length > 0 && !readOnly && !disabled;
	const highlighted = shown && active >= 0 && active < matches.length ? active : -1;

	const close = () => {
		setOpen(false);
		setActive(-1);
	};

	const pick = (o: ChoiceOption) => {
		close();
		onPick(o.value);
	};

	const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
		const composing = e.nativeEvent.isComposing || e.keyCode === 229;
		if (!composing && !readOnly && !disabled) {
			if (e.key === "ArrowDown" || e.key === "ArrowUp") {
				e.preventDefault();
				const n = matches.length;
				const down = e.key === "ArrowDown";
				if (!shown) {
					setOpen(true);
					setActive(down ? 0 : n - 1);
					return;
				}
				// -1 sits between the last row and the first: the typed text, unpicked.
				if (down) setActive(highlighted + 1 >= n ? -1 : highlighted + 1);
				else setActive(highlighted === -1 ? n - 1 : highlighted - 1);
				return;
			}
			if (e.key === "Enter" && highlighted >= 0) {
				e.preventDefault();
				pick(matches[highlighted]);
				return;
			}
			if (e.key === "Escape" && shown) {
				e.preventDefault();
				close();
				return;
			}
		}
		onKeyDown?.(e);
	};

	return (
		<PopoverPrimitive.Root open={shown} onOpenChange={(next) => (next ? setOpen(true) : close())}>
			<PopoverPrimitive.Anchor asChild>
				<div ref={anchor} data-slot="autocomplete" className={cn("w-full", className)}>
					<Input
						id={id}
						role="combobox"
						aria-autocomplete="list"
						aria-expanded={shown}
						aria-controls={shown ? listId : undefined}
						aria-activedescendant={highlighted >= 0 ? `${listId}-${highlighted}` : undefined}
						autoComplete="off"
						size={size}
						invalid={invalid}
						readOnly={readOnly}
						disabled={disabled}
						value={value}
						onChange={(e) => {
							onValueChange(e.target.value);
							setOpen(true);
							setActive(-1);
						}}
						onKeyDown={handleKeyDown}
						onBlur={(e) => {
							close();
							onBlur?.(e);
						}}
						{...props}
					/>
				</div>
			</PopoverPrimitive.Anchor>
			<PopoverPrimitive.Portal>
				<PopoverPrimitive.Content
					data-slot="autocomplete-content"
					align="start"
					sideOffset={4}
					onOpenAutoFocus={(e) => e.preventDefault()}
					onCloseAutoFocus={(e) => e.preventDefault()}
					onInteractOutside={(e) => {
						// The field is outside the list but owns it: a press there keeps it.
						if (anchor.current?.contains(e.target as Node)) e.preventDefault();
					}}
					className={cn(
						"z-50 w-[var(--radix-popover-trigger-width)] min-w-[8rem] overflow-hidden rounded-md",
						"bg-bg-elevated text-text-primary border border-border-default shadow-floating",
						"data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:duration-base data-[state=open]:ease-out",
						"data-[side=bottom]:slide-in-from-top-1 data-[side=top]:slide-in-from-bottom-1",
					)}
				>
					<div
						id={listId}
						role="listbox"
						data-slot="autocomplete-list"
						className="max-h-72 overflow-y-auto overflow-x-hidden p-1"
					>
						{matches.map((o, i) => (
							// biome-ignore lint/a11y/useKeyWithClickEvents: keys reach a row through the field (aria-activedescendant).
							<div
								key={o.value}
								id={`${listId}-${i}`}
								role="option"
								aria-selected={i === highlighted}
								data-selected={i === highlighted || undefined}
								data-slot="autocomplete-item"
								tabIndex={-1}
								className={comboboxItemClass}
								onMouseDown={(e) => e.preventDefault()}
								onMouseMove={() => setActive(i)}
								onClick={() => pick(o)}
							>
								{o.label}
							</div>
						))}
					</div>
				</PopoverPrimitive.Content>
			</PopoverPrimitive.Portal>
		</PopoverPrimitive.Root>
	);
}
