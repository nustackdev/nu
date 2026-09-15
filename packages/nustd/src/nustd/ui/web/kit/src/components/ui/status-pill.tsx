// StatusPill primitive. Compact status indicator: icon + label.
//
// Design refs:
//   primitives.md    §StatusPill (variants danger/warn/ok/info/neutral)
//   palette.md       §2.6 status wash/line/fg
//   space-radius.md  §Density StatusPill (radius full, pad tight)
//   a11y.md          §7 icon paired with color for color-blind safety
//
// Every tone renders a default lucide icon so the semantic reads without
// color: AlertTriangle (danger), Info (warn/info), Check (ok), Circle
// (neutral). Consumers can override via the `icon` prop.

import { cva, type VariantProps } from "class-variance-authority";
import { Slot as SlotPrimitive } from "radix-ui";
import {
	AlertTriangle,
	Check,
	Circle,
	Info,
	type LucideIcon,
} from "lucide-react";
import type * as React from "react";

import { cn } from "../../lib/utils";

const statusPillVariants = cva(
	[
		"inline-flex items-center gap-1 whitespace-nowrap w-fit shrink-0",
		"rounded-full border font-medium tracking-[0.01em] leading-none",
		"transition-colors duration-fast ease-out",
		"[&>svg]:pointer-events-none [&>svg]:shrink-0",
	].join(" "),
	{
		variants: {
			tone: {
				neutral:
					"bg-bg-elevated text-text-secondary border-border-default [&>svg]:text-text-muted",
				info: "bg-status-info-wash text-status-info border-status-info-line [&>svg]:text-status-info",
				ok: "bg-status-ok-wash text-status-ok border-status-ok-line [&>svg]:text-status-ok",
				warn: "bg-status-warn-wash text-status-warn border-status-warn-line [&>svg]:text-status-warn",
				danger:
					"bg-status-danger-wash text-status-danger border-status-danger-line [&>svg]:text-status-danger",
			},
			size: {
				sm: "text-xs px-1.5 py-0.5 [&>svg]:size-3",
				md: "text-xs px-2 py-0.5 [&>svg]:size-3.5",
			},
		},
		defaultVariants: {
			tone: "neutral",
			size: "md",
		},
	},
);

type Tone = NonNullable<VariantProps<typeof statusPillVariants>["tone"]>;

const ICON_MAP: Record<Tone, LucideIcon> = {
	neutral: Circle,
	info: Info,
	ok: Check,
	warn: Info,
	danger: AlertTriangle,
};

export interface StatusPillProps
	extends React.HTMLAttributes<HTMLSpanElement>,
		VariantProps<typeof statusPillVariants> {
	asChild?: boolean;
	icon?: LucideIcon;
}

export function StatusPill({
	className,
	tone,
	size,
	asChild = false,
	icon,
	children,
	...props
}: StatusPillProps) {
	const Comp = asChild ? SlotPrimitive.Root : "span";
	const effectiveTone: Tone = tone ?? "neutral";
	const Icon = icon ?? ICON_MAP[effectiveTone];
	return (
		<Comp
			data-slot="status-pill"
			data-tone={effectiveTone}
			className={cn(statusPillVariants({ tone: effectiveTone, size }), className)}
			{...props}
		>
			<Icon aria-hidden="true" />
			{children}
		</Comp>
	);
}

export { statusPillVariants };
