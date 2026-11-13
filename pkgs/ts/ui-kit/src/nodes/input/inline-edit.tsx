// InlineEditRef -- text that reads as plain text and edits in place.
//
// At rest it is the text itself (the placeholder, muted, while empty), on a
// button: a click, Enter or Space opens the kit InlineEdit over it with the
// text selected. In the editor Enter saves and submits (a change, if the
// text moved, then `{event: "submit"}`, then the enclosing Form's submit),
// a blur saves (a change, if it moved), Escape cancels and puts the text
// back. Enter and Escape hand focus back to the text; a blur leaves it
// where the click went.
//
// The value lands in the store when the edit is saved, not per keystroke: a
// read while the editor is open sees the saved text, which is what an
// Escape would leave. A required one saved empty is a cancel.
//
// `error` draws a kit FieldError under the text and turns the editor red
// (the text at rest stays plain, the error line says it);
// inside a Field the Field's error does the same. Readonly draws the text
// as plain text, not a button; disabled draws a disabled button.

import { Pencil } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";
import { FieldError, Label } from "../../components/ui/field";
import { InlineEdit } from "../../components/ui/inline-edit";
import { cn } from "../../lib/utils";
import { type NodeEntry, type NodeProps, useProp, useStringProp } from "../../tree";
import { asText, type InputSize, resetHandler, useCommit, useControl, valueWrite } from "./control";

// The text at rest and the editor share one height and one text size per
// control size, so opening the editor does not move the line.
const BOX: Record<InputSize, string> = {
	sm: "h-6 text-sm",
	md: "h-8 text-lg",
	lg: "h-10 text-lg",
};

function InlineEditView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	// The program's error, else the message a form's check left.
	const given = useStringProp(path, "error");
	const check = useStringProp(path, "check");
	const error = given || check;
	const maxLength = useProp<number | null>(path, "max_length", null);
	const c = useControl(path);
	const { edit, commit, submit } = useCommit(path);
	const [editing, setEditing] = useState(false);
	const shown = useRef<HTMLButtonElement | null>(null);
	const box = useRef<HTMLDivElement | null>(null);
	const refocus = useRef(false);
	const own = useId();
	const labelId = `${own}-label`;
	const textId = `${own}-text`;
	const errorId = `${own}-error`;

	useEffect(() => {
		if (editing || !refocus.current) return;
		refocus.current = false;
		shown.current?.focus();
	}, [editing]);

	const invalid = c.invalid || error !== "";
	const describedBy = [c.describedBy, error ? errorId : undefined].filter(Boolean).join(" ");
	const labelledBy = c.labelledBy ?? (c.label ? labelId : undefined);
	const locked = c.disabled || c.readOnly;

	const close = (back: boolean) => {
		refocus.current = back;
		setEditing(false);
	};

	const save = (next: string, how: "enter" | "blur") => {
		if (c.required && next.trim() === "") {
			close(how === "enter");
			return;
		}
		edit(next);
		if (how === "enter") submit(box.current);
		else commit();
		close(how === "enter");
	};

	const text = (
		<span id={textId} className={cn("min-w-0 truncate", !value && "text-text-muted")}>
			{value || c.placeholder || " "}
		</span>
	);
	const atRest = "flex w-full min-w-0 items-center gap-1.5 rounded-md border px-1 text-left";

	return (
		<div ref={box} data-slot="inline-edit-ref" className="flex min-w-0 flex-col gap-1">
			{c.label && (
				<Label id={labelId} htmlFor={c.id} required={c.required} disabled={c.disabled}>
					{c.label}
				</Label>
			)}
			{editing ? (
				<span className={cn("flex min-w-0", BOX[c.size])}>
					<InlineEdit
						initial={value}
						label={c.label || c.placeholder || "Edit"}
						className={BOX[c.size]}
						onCommit={save}
						onCancel={() => close(true)}
						inputProps={{
							id: c.id,
							"aria-labelledby": labelledBy,
							"aria-describedby": describedBy || undefined,
							"aria-required": c.required || undefined,
							invalid,
							required: c.required,
							placeholder: c.placeholder,
							maxLength: maxLength ?? undefined,
						}}
					/>
				</span>
			) : c.readOnly ? (
				<span className={cn(atRest, "border-transparent text-text-primary", BOX[c.size])}>
					{text}
				</span>
			) : (
				<button
					ref={shown}
					type="button"
					id={c.id}
					// biome-ignore lint/a11y/noAutofocus: the program asked for it (autofocus=True).
					autoFocus={c.autoFocus}
					disabled={c.disabled}
					aria-labelledby={labelledBy ? `${labelledBy} ${textId}` : undefined}
					aria-describedby={describedBy || undefined}
					onClick={() => {
						if (!locked) setEditing(true);
					}}
					className={cn(
						atRest,
						"group cursor-text text-text-primary",
						"transition-colors duration-fast ease-out hover:bg-bg-hover",
						"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring",
						"disabled:cursor-not-allowed disabled:opacity-50",
						"border-transparent",
						BOX[c.size],
					)}
				>
					{text}
					<Pencil
						aria-hidden
						className="size-3.5 shrink-0 text-text-muted opacity-0 transition-opacity duration-fast group-hover:opacity-100 group-focus-visible:opacity-100"
					/>
				</button>
			)}
			{error ? <FieldError id={errorId}>{error}</FieldError> : null}
		</div>
	);
}

export const InlineEditRef: NodeEntry = {
	component: InlineEditView,
	fill: true,
	input: { empty: "", ownsError: true },
	handlers: {
		write: valueWrite(asText),
		reset: resetHandler,
	},
};
