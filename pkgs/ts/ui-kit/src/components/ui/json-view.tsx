// JsonView primitive.
//
// Thin wrapper over @uiw/react-json-view. Themes it against our semantic
// tokens by mapping the library's inline style keys to kit CSS custom
// properties. `collapsed` is the library's prop for default collapse depth;
// pass `collapseAll` for the read-only shape.
//
// The library's copy is a button per row that shows on hover. Touch mode
// (../../lib/touch.ts) has no hover, so there the rows carry none and one
// copy of the whole value stands in the corner instead, always shown, the
// way a code block's does. A host that draws its own copy of the whole value
// turns that one off with `copyAll={false}`.
//
// Every copy goes through the kit's `copyText` (../../lib/clipboard.ts), the
// library's row copies included: the row icon is drawn here, so it turns to
// a check only when the text got there.

import ReactJsonView from "@uiw/react-json-view";
import { Check, Copy } from "lucide-react";
import type * as React from "react";
import { useState } from "react";

import { copyText } from "../../lib/clipboard";
import { useTouch } from "../../lib/touch";
import { cn } from "../../lib/utils";
import { CopyButton } from "./code";

// The library merges this object over its defaults. Keys are its own literal
// style hooks; values reference our tokens through CSS variables so the theme
// switches with .dark automatically.
const jsonViewStyle: Record<string, string> = {
	"--w-rjv-font-family": "var(--font-mono)",
	"--w-rjv-color": "var(--text-primary)",
	"--w-rjv-key-string": "var(--text-primary)",
	"--w-rjv-key-number": "var(--text-primary)",
	"--w-rjv-background-color": "transparent",
	"--w-rjv-line-color": "var(--border-subtle)",
	"--w-rjv-arrow-color": "var(--text-secondary)",
	"--w-rjv-edit-color": "var(--text-secondary)",
	"--w-rjv-info-color": "var(--text-muted)",
	"--w-rjv-update-color": "var(--accent-text)",
	"--w-rjv-copied-color": "var(--text-secondary)",
	"--w-rjv-copied-success-color": "var(--status-ok)",
	"--w-rjv-quotes-color": "var(--text-muted)",
	"--w-rjv-quotes-string-color": "var(--status-info)",
	"--w-rjv-type-string-color": "var(--status-info)",
	"--w-rjv-type-int-color": "var(--accent-2)",
	"--w-rjv-type-float-color": "var(--accent-2)",
	"--w-rjv-type-bigint-color": "var(--accent-2)",
	"--w-rjv-type-boolean-color": "var(--status-ok)",
	"--w-rjv-type-null-color": "var(--text-muted)",
	"--w-rjv-type-nan-color": "var(--status-danger)",
	"--w-rjv-type-undefined-color": "var(--text-muted)",
	"--w-rjv-type-url-color": "var(--accent-2)",
	"--w-rjv-curlybraces-color": "var(--text-secondary)",
	"--w-rjv-brackets-color": "var(--text-secondary)",
	"--w-rjv-colon-color": "var(--text-secondary)",
	"--w-rjv-ellipsis-color": "var(--text-muted)",
};

export interface JsonViewProps
	extends Omit<React.HTMLAttributes<HTMLDivElement>, "style"> {
	value: unknown;
	collapsed?: number | boolean;
	collapseAll?: boolean;
	displayDataTypes?: boolean;
	displayObjectSize?: boolean;
	size?: "sm" | "md";
	style?: React.CSSProperties;
	/** Touch mode only: the corner copy of the whole value. On by default. */
	copyAll?: boolean;
}

// The whole value as the copy hands it out: indented, the way it reads.
function jsonText(value: unknown): string {
	try {
		return JSON.stringify(value ?? {}, null, 2) ?? "";
	} catch {
		return String(value);
	}
}

// One row's value as its copy hands it out, the way the library spells it:
// a string, number or literal as JSON, a branch indented.
function rowText(value: unknown): string {
	if (typeof value === "number" && !Number.isFinite(value)) return String(value);
	if (typeof value === "bigint") return `${value}n`;
	if (value instanceof Date) return value.toLocaleString();
	try {
		return (
			JSON.stringify(value, (_, v) => (typeof v === "bigint" ? `${v}n` : v), 2) ?? String(value)
		);
	} catch {
		return String(value);
	}
}

// The copy at the end of a row, shown while the row is hovered. Takes the
// library's look (size, spacing, class) and none of its click.
type RowLook = React.SVGProps<SVGSVGElement> & { "data-copied"?: boolean };

function RowCopy({ look, value }: { look: RowLook; value: unknown }) {
	const [copied, setCopied] = useState(false);
	const { onClick: _click, fill: _fill, "data-copied": _copied, ...rest } = look;
	const Icon = copied ? Check : Copy;
	return (
		<Icon
			{...rest}
			aria-hidden="true"
			color={copied ? "var(--w-rjv-copied-success-color)" : "var(--w-rjv-copied-color)"}
			onClick={(e) => {
				e.stopPropagation();
				void copyText(rowText(value)).then((ok) => {
					if (!ok) return;
					setCopied(true);
					window.setTimeout(() => setCopied(false), 1200);
				});
			}}
		/>
	);
}

// The library calls this for each row copy in place of its own.
const renderRowCopy = (look: object, { value }: { value?: unknown }): React.ReactNode => (
	<RowCopy look={look as RowLook} value={value} />
);

function JsonView({
	value,
	collapsed,
	collapseAll = false,
	displayDataTypes = false,
	displayObjectSize = true,
	size = "sm",
	className,
	style,
	copyAll = true,
	...props
}: JsonViewProps) {
	const touch = useTouch();
	const clipboard = !collapseAll;
	const collapsedValue = collapseAll ? true : collapsed;
	const mergedStyle: React.CSSProperties = {
		...(jsonViewStyle as unknown as React.CSSProperties),
		...(style ?? {}),
	};
	return (
		<div
			data-slot="json-view"
			className={cn(
				"w-full font-mono",
				touch && "relative",
				size === "sm" ? "text-xs" : "text-sm",
				className,
			)}
			{...props}
		>
			<ReactJsonView
				value={(value ?? {}) as object}
				collapsed={collapsedValue}
				displayDataTypes={displayDataTypes}
				displayObjectSize={displayObjectSize}
				enableClipboard={clipboard && !touch}
				style={mergedStyle}
			>
				<ReactJsonView.Copied render={renderRowCopy} />
			</ReactJsonView>
			{touch && clipboard && copyAll ? (
				<CopyButton text={jsonText(value)} label="Copy JSON" />
			) : null}
		</div>
	);
}

export { JsonView };
