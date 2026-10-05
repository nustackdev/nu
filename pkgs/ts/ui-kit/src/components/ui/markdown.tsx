// Markdown primitive.
//
// A markdown document on the kit's reading surface. The value is a markdown
// string and the source is never shown: read-only it renders the document,
// `readOnly={false}` makes the same view a live wysiwyg editor. One engine
// (lib/markdown) for both, so a document looks the same whether or not you
// can type in it. Styling is all `Prose`; this adds only the engine.

import type * as React from "react";

import { ProseEditor, type ProseEditorProps } from "../../lib/markdown/editor";
import { Prose } from "./prose";

export interface MarkdownProps
	extends Omit<ProseEditorProps, "onCommit" | "readOnly" | "className">,
		Omit<React.HTMLAttributes<HTMLDivElement>, "placeholder"> {
	/** On by default: a document reads unless told it may be edited. */
	readOnly?: boolean;
	/** Fires on a quiet moment and on blur, only when the document changed. */
	onCommit?: (source: string) => void;
}

function Markdown({
	value,
	placeholder,
	readOnly = true,
	onCommit,
	schema,
	onView,
	className,
	...props
}: MarkdownProps) {
	return (
		<Prose data-slot="markdown" className={className} {...props}>
			<ProseEditor
				value={value}
				placeholder={placeholder}
				readOnly={readOnly}
				onCommit={onCommit ?? noop}
				schema={schema}
				onView={onView}
			/>
		</Prose>
	);
}

function noop(): void {}

export { Markdown };
