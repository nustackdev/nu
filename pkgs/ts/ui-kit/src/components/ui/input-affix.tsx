// InputAffix: a kit Input with a glyph or a small control inside its border,
// before the text (`leading`) or after it (`trailing`). The Input keeps its
// look, its sizes and every native prop; the affix only pads the text clear
// of what sits on top of it.
//
// Two fields are built on it:
//
// - SearchInput: a search field with a magnifier before the text and a
//   clear button after it while there is text. Escape clears too, so the
//   clear button stays out of the Tab order (a mouse shortcut for what the
//   keyboard already has). The browser's own clear glyph is hidden.
// - PasswordInput: a password field with a show / hide toggle after the
//   text. The toggle is a real button in the Tab order, one name ("Show
//   password") and `aria-pressed` while the password shows, so a screen
//   reader hears the state and not a name that flips.
//
// Neither button takes focus from the field on a click (mouse down is held
// back), so clearing or revealing never blurs, and never commits, the field.

import { Eye, EyeOff, Search, X } from "lucide-react";
import * as React from "react";
import { cn } from "../../lib/utils";
import { IconButton } from "./icon-button";
import { Input, type InputProps } from "./input";

type Size = "sm" | "md" | "lg";

// Room the text keeps clear of an affix, per size: the affix's width plus
// the Input's own pad.
const PAD_START: Record<Size, string> = { sm: "pl-6", md: "pl-8", lg: "pl-9" };
const PAD_END: Record<Size, string> = { sm: "pr-6", md: "pr-8", lg: "pr-9" };
const SIDE_START: Record<Size, string> = { sm: "left-2", md: "left-2.5", lg: "left-3" };
const GLYPH: Record<Size, string> = {
	sm: "[&_svg]:size-3",
	md: "[&_svg]:size-3.5",
	lg: "[&_svg]:size-4",
};
const SIDE_END: Record<Size, string> = { sm: "right-0.5", md: "right-1", lg: "right-1.5" };

/** The icon button size that sits inside an input of a given size. */
const BUTTON: Record<Size, "xs" | "sm" | "md"> = { sm: "xs", md: "sm", lg: "sm" };

export interface InputAffixProps extends InputProps {
	/** Drawn before the text, usually a glyph. Not interactive. */
	leading?: React.ReactNode;
	/** Drawn after the text, usually an icon button. */
	trailing?: React.ReactNode;
}

export function InputAffix({ leading, trailing, size, className, ...props }: InputAffixProps) {
	const s: Size = size ?? "md";
	return (
		<div data-slot="input-affix" className="relative flex w-full min-w-0 items-center">
			{leading ? (
				<span
					aria-hidden
					className={cn(
						"pointer-events-none absolute inset-y-0 flex items-center text-text-muted",
						SIDE_START[s],
						GLYPH[s],
					)}
				>
					{leading}
				</span>
			) : null}
			<Input
				size={s}
				className={cn(leading && PAD_START[s], trailing && PAD_END[s], className)}
				{...props}
			/>
			{trailing ? (
				<span className={cn("absolute inset-y-0 flex items-center", SIDE_END[s])}>{trailing}</span>
			) : null}
		</div>
	);
}

// A button inside a field: clicking it never moves focus off the field.
function keepFocus(e: React.MouseEvent) {
	e.preventDefault();
}

export interface SearchInputProps extends Omit<InputProps, "type" | "value"> {
	value: string;
	/** Clear the text: the clear button, or Escape while there is text. */
	onClear: () => void;
	/** The clear button's name. */
	clearLabel?: string;
}

export function SearchInput({
	value,
	onClear,
	clearLabel = "Clear",
	size,
	className,
	onKeyDown,
	...props
}: SearchInputProps) {
	const s: Size = size ?? "md";
	const clearable = value !== "" && !props.disabled && !props.readOnly;
	return (
		<InputAffix
			{...props}
			type="search"
			size={s}
			value={value}
			className={cn("[&::-webkit-search-cancel-button]:appearance-none", className)}
			leading={<Search />}
			trailing={
				clearable ? (
					<IconButton
						variant="ghost"
						size={BUTTON[s]}
						aria-label={clearLabel}
						tabIndex={-1}
						onMouseDown={keepFocus}
						onClick={onClear}
					>
						<X />
					</IconButton>
				) : null
			}
			onKeyDown={(e) => {
				onKeyDown?.(e);
				if (e.defaultPrevented || e.key !== "Escape" || !clearable) return;
				e.preventDefault();
				onClear();
			}}
		/>
	);
}

export interface PasswordInputProps extends Omit<InputProps, "type"> {
	/** The toggle's name. */
	showLabel?: string;
}

export function PasswordInput({ showLabel = "Show password", size, ...props }: PasswordInputProps) {
	const s: Size = size ?? "md";
	const [shown, setShown] = React.useState(false);
	return (
		<InputAffix
			{...props}
			type={shown ? "text" : "password"}
			size={s}
			autoComplete={props.autoComplete ?? "current-password"}
			trailing={
				<IconButton
					variant="ghost"
					size={BUTTON[s]}
					aria-label={showLabel}
					aria-pressed={shown}
					aria-controls={props.id}
					disabled={props.disabled}
					onMouseDown={keepFocus}
					onClick={() => setShown((v) => !v)}
				>
					{shown ? <EyeOff /> : <Eye />}
				</IconButton>
			}
		/>
	);
}
