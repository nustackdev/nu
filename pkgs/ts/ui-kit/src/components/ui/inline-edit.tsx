// InlineEdit: rename in place, on a kit Input shrunk into the row it sits in.
//
// Commits on Enter and on blur (you clicked away, you meant it), cancels on
// Escape, and selects the text on mount so the first keystroke replaces it.
// It reports the raw value; trimming, and deciding an unchanged value is no
// rename, is the caller's call.
//
// Keys are kept from the row around it: arrows, Home and End move the caret
// here, not the focus of a tree or list the row belongs to.

import type * as React from "react";
import { useEffect, useRef } from "react";
import { cn } from "../../lib/utils";
import { Input } from "./input";

export type InlineEditProps = {
	/** The value it opens with. */
	initial: string;
	/** Accessible name, eg "Rename notes.md". */
	label: string;
	/** `how` says whether Enter or a blur committed it, eg to put focus back. */
	onCommit: (value: string, how: "enter" | "blur") => void;
	onCancel: () => void;
	className?: string;
};

export function InlineEdit({ initial, label, onCommit, onCancel, className }: InlineEditProps) {
	const done = useRef(false);
	const input = useRef<HTMLInputElement | null>(null);
	useEffect(() => {
		input.current?.focus();
		input.current?.select();
	}, []);

	const finish = (fn: () => void) => {
		if (done.current) return;
		done.current = true;
		fn();
	};

	return (
		<span data-slot="inline-edit" className="flex min-w-0 flex-1 items-center">
			<Input
				ref={input}
				size="sm"
				ring="inset"
				aria-label={label}
				defaultValue={initial}
				className={cn("h-6 min-w-0 flex-1 px-1 py-0", className)}
				onBlur={(e) => {
					const value = e.currentTarget.value;
					finish(() => onCommit(value, "blur"));
				}}
				onClick={(e) => e.stopPropagation()}
				onDoubleClick={(e) => e.stopPropagation()}
				onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
					e.stopPropagation();
					if (e.key === "Enter") {
						e.preventDefault();
						const value = e.currentTarget.value;
						finish(() => onCommit(value, "enter"));
					} else if (e.key === "Escape") {
						e.preventDefault();
						finish(onCancel);
					}
				}}
			/>
		</span>
	);
}
