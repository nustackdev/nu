import { cva, type VariantProps } from "class-variance-authority";
import { X } from "lucide-react";
import * as React from "react";

import { cn } from "../../lib/utils";

// Multi-value input rendered as chip tokens. No Radix equivalent
// (design/primitives.md §TagInput). Wrapper mirrors Input variants so it
// sits flush next to other form controls.

const tagInputVariants = cva(
	[
		"flex w-full flex-wrap items-center gap-1 rounded-md",
		"border transition-[border-color,box-shadow] duration-fast ease-out",
		"focus-within:outline-hidden focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 focus-within:ring-offset-bg-canvas",
		"cursor-text",
	].join(" "),
	{
		variants: {
			variant: {
				default: "bg-bg-surface text-text-primary border-border-default hover:border-border-strong focus-within:border-border-strong",
				ghost: "bg-transparent text-text-primary border-transparent hover:bg-bg-elevated",
				filled: "bg-bg-elevated text-text-primary border-transparent hover:bg-bg-sunken",
			},
			size: {
				sm: "min-h-6 px-1.5 py-0.5 text-sm",
				md: "min-h-8 px-2 py-1 text-lg",
				lg: "min-h-10 px-2.5 py-1.5 text-lg",
			},
			invalid: {
				true: "border-status-danger focus-within:ring-status-danger",
				false: "",
			},
			disabled: {
				true: "cursor-not-allowed opacity-50 bg-bg-sunken",
				false: "",
			},
		},
		defaultVariants: {
			variant: "default",
			size: "md",
			invalid: false,
			disabled: false,
		},
	},
);

const chipSize = {
	sm: "h-4 px-1 text-xs [&_svg]:size-2.5",
	md: "h-5 px-1.5 text-xs [&_svg]:size-3",
	lg: "h-6 px-2 text-sm [&_svg]:size-3.5",
} as const;

type TagInputSize = keyof typeof chipSize;

interface TagInputProps
	extends Omit<
			React.InputHTMLAttributes<HTMLInputElement>,
			"value" | "onChange" | "size" | "disabled"
		>,
		VariantProps<typeof tagInputVariants> {
	value: string[];
	onValueChange: (value: string[]) => void;
	maxTags?: number;
	disabled?: boolean;
	invalid?: boolean;
	size?: TagInputSize;
}

function TagInput({
	className,
	variant,
	size = "md",
	invalid,
	disabled,
	value,
	onValueChange,
	maxTags,
	placeholder,
	onKeyDown,
	...props
}: TagInputProps) {
	const inputRef = React.useRef<HTMLInputElement>(null);
	const [draft, setDraft] = React.useState("");

	const commit = React.useCallback(
		(raw: string) => {
			const clean = raw.trim();
			if (!clean) return;
			if (value.includes(clean)) {
				setDraft("");
				return;
			}
			if (maxTags !== undefined && value.length >= maxTags) return;
			onValueChange([...value, clean]);
			setDraft("");
		},
		[maxTags, onValueChange, value],
	);

	const removeAt = React.useCallback(
		(index: number) => {
			onValueChange(value.filter((_, i) => i !== index));
		},
		[onValueChange, value],
	);

	const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
		onKeyDown?.(event);
		if (event.defaultPrevented) return;
		if (event.key === "Enter" || event.key === ",") {
			event.preventDefault();
			commit(draft);
			return;
		}
		if (event.key === "Backspace" && draft === "" && value.length > 0) {
			event.preventDefault();
			removeAt(value.length - 1);
		}
	};

	const handleBlur = (event: React.FocusEvent<HTMLInputElement>) => {
		commit(draft);
		props.onBlur?.(event);
	};

	return (
		<div
			data-slot="tag-input"
			data-invalid={invalid || undefined}
			className={cn(tagInputVariants({ variant, size, invalid, disabled, className }))}
			onClick={() => inputRef.current?.focus()}
			onKeyDown={(event) => {
				if (event.target === event.currentTarget) inputRef.current?.focus();
			}}
			role="group"
			aria-disabled={disabled || undefined}
		>
			{value.map((tag, index) => (
				<span
					// tags are unique after commit(); index disambiguates duplicates
					// that could arrive from external onValueChange updates.
					key={`${tag}-${index}`}
					data-slot="tag-input-chip"
					className={cn(
						"inline-flex items-center gap-1 rounded-sm bg-accent-wash text-text-primary border border-accent-line font-medium",
						chipSize[size],
					)}
				>
					<span className="truncate">{tag}</span>
					<button
						type="button"
						aria-label={`Remove ${tag}`}
						disabled={disabled}
						className={cn(
							"inline-flex items-center justify-center rounded-sm text-text-secondary hover:text-text-primary",
							"focus:outline-hidden focus-visible:ring-1 focus-visible:ring-ring",
							"disabled:pointer-events-none",
						)}
						onClick={(event) => {
							event.stopPropagation();
							removeAt(index);
						}}
					>
						<X />
					</button>
				</span>
			))}
			<input
				ref={inputRef}
				data-slot="tag-input-field"
				type="text"
				className={cn(
					"flex-1 min-w-24 bg-transparent outline-hidden",
					"text-text-primary placeholder:text-text-muted",
					"disabled:cursor-not-allowed",
				)}
				value={draft}
				onChange={(event) => setDraft(event.target.value)}
				onKeyDown={handleKeyDown}
				onBlur={handleBlur}
				disabled={disabled}
				placeholder={value.length === 0 ? placeholder : undefined}
				aria-invalid={invalid || undefined}
				{...props}
			/>
		</div>
	);
}

export { TagInput, tagInputVariants };
