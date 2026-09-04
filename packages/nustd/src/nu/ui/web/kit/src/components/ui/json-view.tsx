// JsonView primitive.
//
// Thin wrapper over @uiw/react-json-view. Themes it against our semantic
// tokens by mapping the library's inline style keys to kit CSS custom
// properties. `collapsed` is the library's prop for default collapse depth;
// pass `collapseAll` for the read-only shape.

import ReactJsonView from "@uiw/react-json-view";
import type * as React from "react";

import { cn } from "../../lib/utils";

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
	"--w-rjv-update-color": "var(--accent)",
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
}

function JsonView({
	value,
	collapsed,
	collapseAll = false,
	displayDataTypes = false,
	displayObjectSize = true,
	size = "sm",
	className,
	style,
	...props
}: JsonViewProps) {
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
				enableClipboard={!collapseAll}
				style={mergedStyle}
			/>
		</div>
	);
}

export { JsonView };
