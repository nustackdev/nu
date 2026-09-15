import { cva, type VariantProps } from "class-variance-authority";
import { Minus, Plus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import type * as React from "react";

import { cn } from "../../lib/utils";

// Matching Input sm/md/lg row heights per space-radius.md §Density Input.
const numberInputVariants = cva(
	[
		"inline-flex items-center gap-1 rounded-md",
		"border border-border-default bg-bg-surface",
		"transition-[border-color,box-shadow] duration-fast ease-out",
		"hover:border-border-strong",
		"focus-within:border-border-strong",
		"focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 focus-within:ring-offset-bg-canvas",
		"has-[input:disabled]:opacity-50 has-[input:disabled]:cursor-not-allowed",
		"aria-invalid:border-status-danger",
	].join(" "),
	{
		variants: {
			size: {
				sm: "h-6 px-2 text-sm",
				md: "h-8 px-2.5 text-base",
				lg: "h-10 px-3 text-lg",
			},
			variant: {
				default: "",
				ghost: "bg-transparent border-transparent hover:bg-bg-sunken",
				filled: "bg-bg-sunken border-transparent",
			},
		},
		defaultVariants: {
			size: "md",
			variant: "default",
		},
	},
);

const stepperSizes = {
	sm: "size-4 [&_svg]:size-3",
	md: "size-5 [&_svg]:size-3.5",
	lg: "size-6 [&_svg]:size-4",
} as const;

export interface NumberInputProps
	extends Omit<
			React.InputHTMLAttributes<HTMLInputElement>,
			"value" | "onChange" | "type" | "size"
		>,
		VariantProps<typeof numberInputVariants> {
	value?: number | null;
	onValueChange?: (value: number | null) => void;
	min?: number;
	max?: number;
	step?: number;
	invalid?: boolean;
	steppers?: boolean;
}

// Kept a text input with numeric inputMode + pattern so browser step arrows and
// scroll-wheel-changes-value never appear. See primitives.md §NumberInput.
export function NumberInput({
	className,
	size,
	variant,
	value,
	onValueChange,
	min,
	max,
	step = 1,
	disabled,
	invalid,
	steppers = true,
	onBlur,
	...props
}: NumberInputProps) {
	const [draft, setDraft] = useState<string>(() =>
		value === null || value === undefined ? "" : String(value),
	);

	// Sync internal draft when the controlled value changes from outside.
	useEffect(() => {
		if (value === null || value === undefined) {
			setDraft("");
			return;
		}
		const parsed = draft === "" ? null : Number(draft);
		if (parsed !== value) setDraft(String(value));
	}, [value, draft]);

	const clamp = useCallback(
		(n: number) => {
			let out = n;
			if (typeof min === "number" && out < min) out = min;
			if (typeof max === "number" && out > max) out = max;
			return out;
		},
		[min, max],
	);

	const emit = useCallback(
		(next: number | null) => {
			onValueChange?.(next);
		},
		[onValueChange],
	);

	const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const raw = e.target.value;
		// Allow empty + partial states while typing (e.g. "-", "1.").
		if (raw === "" || raw === "-") {
			setDraft(raw);
			if (raw === "") emit(null);
			return;
		}
		if (!/^-?\d*(\.\d*)?$/.test(raw)) return;
		setDraft(raw);
		const parsed = Number(raw);
		if (Number.isFinite(parsed)) emit(parsed);
	};

	const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
		if (draft === "" || draft === "-") {
			emit(null);
		} else {
			const parsed = Number(draft);
			if (Number.isFinite(parsed)) {
				const clamped = clamp(parsed);
				setDraft(String(clamped));
				if (clamped !== parsed) emit(clamped);
			}
		}
		onBlur?.(e);
	};

	const bump = (delta: number) => {
		const base =
			draft === "" || draft === "-" ? 0 : Number(draft);
		if (!Number.isFinite(base)) return;
		const next = clamp(base + delta);
		setDraft(String(next));
		emit(next);
	};

	const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
		if (e.key === "ArrowUp") {
			e.preventDefault();
			bump(e.shiftKey ? step * 10 : step);
		} else if (e.key === "ArrowDown") {
			e.preventDefault();
			bump(e.shiftKey ? -step * 10 : -step);
		}
	};

	return (
		<div
			data-slot="number-input"
			aria-invalid={invalid || undefined}
			className={cn(numberInputVariants({ size, variant }), className)}
		>
			<input
				{...props}
				type="text"
				inputMode="decimal"
				pattern="-?\d*(\.\d+)?"
				value={draft}
				disabled={disabled}
				aria-invalid={invalid || undefined}
				onChange={handleChange}
				onBlur={handleBlur}
				onKeyDown={handleKeyDown}
				className={cn(
					"min-w-0 flex-1 bg-transparent text-text-primary placeholder:text-text-muted",
					"outline-none disabled:cursor-not-allowed",
				)}
			/>
			{steppers ? (
				<div className="flex shrink-0 items-center gap-0.5">
					<button
						type="button"
						tabIndex={-1}
						disabled={disabled}
						onClick={() => bump(-step)}
						aria-label="Decrement"
						className={cn(
							"inline-flex items-center justify-center rounded-sm text-text-secondary",
							"transition-colors duration-fast ease-out",
							"hover:bg-bg-elevated hover:text-text-primary",
							"disabled:pointer-events-none disabled:opacity-50",
							stepperSizes[size ?? "md"],
						)}
					>
						<Minus />
					</button>
					<button
						type="button"
						tabIndex={-1}
						disabled={disabled}
						onClick={() => bump(step)}
						aria-label="Increment"
						className={cn(
							"inline-flex items-center justify-center rounded-sm text-text-secondary",
							"transition-colors duration-fast ease-out",
							"hover:bg-bg-elevated hover:text-text-primary",
							"disabled:pointer-events-none disabled:opacity-50",
							stepperSizes[size ?? "md"],
						)}
					>
						<Plus />
					</button>
				</div>
			) : null}
		</div>
	);
}

export { numberInputVariants };
