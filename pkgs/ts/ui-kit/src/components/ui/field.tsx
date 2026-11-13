import { TriangleAlert } from "lucide-react";
import * as React from "react";
import { cn } from "../../lib/utils";

// Field chrome per a11y.md §5: one label tied to the control, help that stays,
// an error that announces itself, and the ids that wire them together.
//
// `Field` owns the ids. It derives `<id>`, `<id>-help` and `<id>-error` from
// `useId()` (or the `id` it is given) and hands them, with the field's
// invalid / required / disabled state, to whatever control sits inside through
// `FieldContext`. A control reads `useFieldControl()` and spreads what it gets
// onto the real element, so `aria-invalid`, `aria-describedby` and `required`
// land on the input and never on a wrapper. Outside a Field the hook returns
// null and the control draws on its own props.

export type FieldState = {
	/** The control's id; `Label` points here. */
	id: string;
	/** The label's own id, for a group control a `<label for>` cannot name (`aria-labelledby`). */
	labelId: string;
	helpId: string;
	errorId: string;
	/** Space-joined ids for `aria-describedby`, or undefined when there is nothing. */
	describedBy: string | undefined;
	invalid: boolean;
	required: boolean;
	disabled: boolean;
	/** The field draws a label, so the control should not draw its own. */
	labelled: boolean;
};

export const FieldContext = React.createContext<FieldState | null>(null);

/** The surrounding Field's state, or null outside one. */
export function useFieldControl(): FieldState | null {
	return React.useContext(FieldContext);
}

export interface FieldProps extends React.ComponentProps<"div"> {
	id?: string;
	label?: React.ReactNode;
	help?: React.ReactNode;
	error?: React.ReactNode;
	required?: boolean;
	disabled?: boolean;
}

/**
 * Label, one control, help and error, wired. Help persists above the error;
 * `aria-describedby` on the control lists both.
 */
export function Field({
	id: given,
	label,
	help,
	error,
	required = false,
	disabled = false,
	className,
	children,
	...props
}: FieldProps) {
	const auto = React.useId();
	const id = given ?? auto;
	const hasHelp = help != null && help !== "" && help !== false;
	const hasError = error != null && error !== "" && error !== false;
	const hasLabel = label != null && label !== "" && label !== false;
	const state = React.useMemo<FieldState>(
		() => ({
			id,
			labelId: `${id}-label`,
			helpId: `${id}-help`,
			errorId: `${id}-error`,
			describedBy:
				[hasHelp ? `${id}-help` : null, hasError ? `${id}-error` : null]
					.filter(Boolean)
					.join(" ") || undefined,
			invalid: hasError,
			required,
			disabled,
			labelled: hasLabel,
		}),
		[id, hasHelp, hasError, hasLabel, required, disabled],
	);
	return (
		<FieldContext.Provider value={state}>
			<div data-slot="field" className={cn("flex flex-col gap-1", className)} {...props}>
				{hasLabel ? (
					<Label
						id={`${id}-label`}
						htmlFor={id}
						required={required}
						invalid={hasError}
						disabled={disabled}
					>
						{label}
					</Label>
				) : null}
				{children}
				{hasHelp ? <FieldHelp id={state.helpId}>{help}</FieldHelp> : null}
				{hasError ? <FieldError id={state.errorId}>{error}</FieldError> : null}
			</div>
		</FieldContext.Provider>
	);
}

export interface LabelProps extends React.ComponentProps<"label"> {
	/** Draws the accent asterisk. The control still carries `required` itself. */
	required?: boolean;
	invalid?: boolean;
	disabled?: boolean;
	/** `inline` is the label beside a checkbox, switch or radio: body size, primary ink. */
	inline?: boolean;
}

/** A real `<label>`; pass `htmlFor` the control's id. */
export function Label({
	required,
	invalid,
	disabled,
	inline,
	className,
	children,
	...props
}: LabelProps) {
	return (
		// biome-ignore lint/a11y/noLabelWithoutControl: callers pass htmlFor.
		<label
			data-slot="label"
			className={cn(
				"cursor-default select-none",
				inline ? "text-base text-text-primary" : "text-sm font-medium text-text-secondary",
				invalid && !inline && "text-status-danger",
				disabled && "opacity-50",
				className,
			)}
			{...props}
		>
			{children}
			{required ? (
				<span className="ml-0.5 text-accent-text" aria-hidden>
					*
				</span>
			) : null}
		</label>
	);
}

/** Help under a control. Stays when an error shows. */
export function FieldHelp({ className, ...props }: React.ComponentProps<"p">) {
	return (
		<p data-slot="field-help" className={cn("text-xs text-text-secondary", className)} {...props} />
	);
}

/** An error under a control, announced on first paint (`role="alert"`), with its icon. */
export function FieldError({ className, children, ...props }: React.ComponentProps<"p">) {
	return (
		<p
			data-slot="field-error"
			role="alert"
			className={cn("flex items-start gap-1 text-xs text-status-danger", className)}
			{...props}
		>
			<TriangleAlert aria-hidden className="mt-px size-3 shrink-0" />
			<span>{children}</span>
		</p>
	);
}
