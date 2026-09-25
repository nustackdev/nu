// StatusDot primitive. A bare tone dot, StatusPill without the words.
//
// Tones match StatusPill (neutral/info/ok/warn/danger). A dot is color only,
// so a11y.md §7 is on the caller: pass `label` when nothing next to the dot
// says the state in words, and it becomes a named image; without one it is
// hidden from assistive tech as decoration.
//
// `pulse` is for a live state (connecting, running). The kit's reduced-motion
// rule stops it.

import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";

import { cn } from "../../lib/utils";

const statusDotVariants = cva("inline-block size-2 shrink-0 rounded-full", {
	variants: {
		tone: {
			neutral: "bg-text-muted",
			info: "bg-status-info",
			ok: "bg-status-ok",
			warn: "bg-status-warn",
			danger: "bg-status-danger",
		},
		pulse: {
			true: "animate-pulse",
			false: "",
		},
	},
	defaultVariants: {
		tone: "neutral",
		pulse: false,
	},
});

export interface StatusDotProps
	extends React.ComponentProps<"span">,
		VariantProps<typeof statusDotVariants> {
	label?: string;
}

export function StatusDot({ className, tone, pulse, label, ...props }: StatusDotProps) {
	return (
		<span
			data-slot="status-dot"
			data-tone={tone ?? "neutral"}
			className={cn(statusDotVariants({ tone, pulse }), className)}
			{...(label ? { role: "img", "aria-label": label } : { "aria-hidden": true })}
			{...props}
		/>
	);
}

export { statusDotVariants };
