// Code primitive.
//
// Inline <code> by default. `block` opts into a code surface: the kit's one
// code engine (lib/code), read-only unless told otherwise, with an optional
// copy affordance in the top-right corner. `readOnly={false}` turns the same
// block into an editor, so a sample and an editable buffer never look apart.
//
// The source is `value`, or string children when there is no `value`. Font is
// JetBrains Mono; colors come from the `--syntax-*` tokens, so the `.dark`
// flip restyles every block with no observer. Unknown languages render plain.

import type { EditorView } from "@codemirror/view";
import { Check, Copy } from "lucide-react";
import type * as React from "react";
import { useCallback, useState } from "react";

import { CodeMirrorView } from "../../lib/code/view";
import { cn } from "../../lib/utils";

export interface CodeProps extends Omit<React.HTMLAttributes<HTMLElement>, "onChange"> {
	block?: boolean;
	/** A copy button in the corner of a block. Shown only while read-only. */
	copyable?: boolean;
	/** A language name or alias (`python`, `ts`, `sql`, `shell`). Unknown renders plain. */
	language?: string;
	/** The source. Falls back to string children. */
	value?: string;
	/** Block only. On by default: a block reads unless told it may be edited. */
	readOnly?: boolean;
	/** Block only. Defaults to on while editable, off while read-only. */
	lineNumbers?: boolean;
	/** Block only. Soft-wrap long lines instead of scrolling sideways. */
	wrap?: boolean;
	/** Block only. Height bounds in px; the block grows between them. 0 is no bound. */
	minHeight?: number;
	maxHeight?: number;
	/** Block only. Fires on cmd+enter and on blur, and only when the text changed. */
	onCommit?: (source: string) => void;
	/** Block only. Whether the buffer differs from `value`, on every keystroke. */
	onDirty?: (dirty: boolean) => void;
	/** Block only. The live CodeMirror view on mount, null on teardown. */
	onView?: (view: EditorView | null) => void;
	children?: React.ReactNode;
}

function Code({
	className,
	block = false,
	copyable = false,
	language,
	value,
	readOnly = true,
	lineNumbers,
	wrap,
	minHeight,
	maxHeight,
	onCommit,
	onDirty,
	onView,
	children,
	...props
}: CodeProps) {
	if (block) {
		const source = value ?? (typeof children === "string" ? children : "");
		return (
			<div
				data-slot="code-block"
				data-language={language || undefined}
				data-editable={readOnly ? undefined : ""}
				className={cn(
					"relative w-full overflow-hidden rounded-md bg-bg-sunken border border-border-subtle",
					className,
				)}
				{...props}
			>
				<CodeMirrorView
					value={source}
					language={language}
					readOnly={readOnly}
					lineNumbers={lineNumbers}
					wrap={wrap}
					minHeight={minHeight}
					maxHeight={maxHeight}
					onCommit={onCommit}
					onDirty={onDirty}
					onView={onView}
				/>
				{copyable && readOnly && <CopyButton text={source} />}
			</div>
		);
	}

	return (
		<code
			data-slot="code"
			data-language={language}
			className={cn(
				"font-mono text-sm bg-bg-sunken text-text-primary rounded-sm",
				"px-1 py-0.5 border border-border-subtle",
				className,
			)}
			{...props}
		>
			{value ?? children}
		</code>
	);
}

function CopyButton({ text }: { text: string }) {
	const [copied, setCopied] = useState(false);
	const copy = useCallback(() => {
		void navigator.clipboard?.writeText(text).then(() => {
			setCopied(true);
			// Reset after a brief acknowledgement window.
			window.setTimeout(() => setCopied(false), 1200);
		});
	}, [text]);
	return (
		<button
			type="button"
			onClick={copy}
			aria-label={copied ? "Copied" : "Copy code"}
			className={cn(
				"absolute top-1.5 right-1.5 inline-flex size-6 items-center justify-center",
				"rounded-sm text-text-secondary bg-bg-elevated border border-border-subtle",
				"hover:text-text-primary hover:bg-bg-surface",
				"transition-colors duration-fast ease-out",
				"focus-visible:outline-none focus-ring",
			)}
		>
			{copied ? <Check className="size-3.5 text-status-ok" /> : <Copy className="size-3.5" />}
		</button>
	);
}

export { Code };
