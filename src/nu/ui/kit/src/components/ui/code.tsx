// Code primitive.
//
// Inline <code> by default. `block` opts into a <pre><code> fence with copy
// affordance in the top-right corner. Font is JetBrains Mono; size follows
// typography.md §4 code recipes.

import { Check, Copy } from "lucide-react";
import type * as React from "react";
import { useCallback, useState } from "react";

import { cn } from "../../lib/utils";

export interface CodeProps extends React.HTMLAttributes<HTMLElement> {
	block?: boolean;
	copyable?: boolean;
	language?: string;
	children?: React.ReactNode;
}

function Code({
	className,
	block = false,
	copyable = false,
	language,
	children,
	...props
}: CodeProps) {
	const [copied, setCopied] = useState(false);

	const handleCopy = useCallback(() => {
		if (typeof children !== "string") return;
		void navigator.clipboard?.writeText(children).then(() => {
			setCopied(true);
			// Reset after a brief acknowledgement window.
			window.setTimeout(() => setCopied(false), 1200);
		});
	}, [children]);

	if (block) {
		return (
			<div
				data-slot="code-block"
				data-language={language}
				className={cn(
					"relative w-full rounded-md bg-bg-sunken border border-border-subtle",
					className,
				)}
			>
				<pre className="overflow-x-auto p-3 text-sm font-mono text-text-primary whitespace-pre">
					<code {...props}>{children}</code>
				</pre>
				{copyable && (
					<button
						type="button"
						onClick={handleCopy}
						aria-label={copied ? "Copied" : "Copy code"}
						className={cn(
							"absolute top-1.5 right-1.5 inline-flex size-6 items-center justify-center",
							"rounded-sm text-text-secondary bg-bg-elevated border border-border-subtle",
							"hover:text-text-primary hover:bg-bg-surface",
							"transition-colors duration-fast ease-out",
							"focus-visible:outline-none focus-ring",
						)}
					>
						{copied ? (
							<Check className="size-3.5 text-status-ok" />
						) : (
							<Copy className="size-3.5" />
						)}
					</button>
				)}
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
			{children}
		</code>
	);
}

export { Code };
