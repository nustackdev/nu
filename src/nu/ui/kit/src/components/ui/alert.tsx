// Alert primitive.
//
// Inline message surface, non-modal. AlertDialog (Radix) covers modal confirms.
// Tone drives the wash/line/fg triple + auto icon per a11y.md §7.

import { cva, type VariantProps } from "class-variance-authority";
import {
	AlertTriangle,
	CheckCircle2,
	Info,
	AlertCircle,
	Bell,
	type LucideIcon,
} from "lucide-react";
import * as React from "react";

import { cn } from "../../lib/utils";

const alertVariants = cva(
	[
		"relative w-full rounded-md border p-3 flex gap-3 items-start",
		"text-sm font-display",
		"transition-colors duration-fast ease-out",
	].join(" "),
	{
		variants: {
			tone: {
				neutral: "bg-bg-elevated text-text-primary border-border-default",
				info: "bg-status-info-wash text-text-primary border-status-info-line",
				danger: "bg-status-danger-wash text-text-primary border-status-danger-line",
				warn: "bg-status-warn-wash text-text-primary border-status-warn-line",
				ok: "bg-status-ok-wash text-text-primary border-status-ok-line",
			},
		},
		defaultVariants: {
			tone: "neutral",
		},
	},
);

type AlertTone = NonNullable<VariantProps<typeof alertVariants>["tone"]>;

const ICON_MAP: Record<AlertTone, LucideIcon> = {
	neutral: Bell,
	info: Info,
	danger: AlertTriangle,
	warn: AlertCircle,
	ok: CheckCircle2,
};

const ICON_TONE_CLASS: Record<AlertTone, string> = {
	neutral: "text-text-secondary",
	info: "text-status-info",
	danger: "text-status-danger",
	warn: "text-status-warn",
	ok: "text-status-ok",
};

interface AlertContextValue {
	tone: AlertTone;
}

// Small context so Icon/Title/Description can read the tone their parent set
// without every consumer passing tone down manually.
const AlertContext = React.createContext<AlertContextValue>({ tone: "neutral" });

export interface AlertProps
	extends React.HTMLAttributes<HTMLDivElement>,
		VariantProps<typeof alertVariants> {}

function Alert({ className, tone, children, ...props }: AlertProps) {
	const effectiveTone: AlertTone = tone ?? "neutral";
	return (
		<AlertContext.Provider value={{ tone: effectiveTone }}>
			<div
				role="alert"
				data-slot="alert"
				data-tone={effectiveTone}
				className={cn(alertVariants({ tone: effectiveTone }), className)}
				{...props}
			>
				{children}
			</div>
		</AlertContext.Provider>
	);
}

export interface AlertIconProps extends React.HTMLAttributes<HTMLSpanElement> {
	icon?: LucideIcon;
}

function AlertIcon({ className, icon, ...props }: AlertIconProps) {
	const { tone } = React.useContext(AlertContext);
	const Icon = icon ?? ICON_MAP[tone];
	return (
		<span
			data-slot="alert-icon"
			aria-hidden="true"
			className={cn("shrink-0 mt-0.5", ICON_TONE_CLASS[tone], className)}
			{...props}
		>
			<Icon className="size-4" />
		</span>
	);
}

function AlertTitle({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="alert-title"
			className={cn("font-semibold leading-tight mb-0.5", className)}
			{...props}
		/>
	);
}

function AlertDescription({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
	return (
		<div
			data-slot="alert-description"
			className={cn("text-text-secondary leading-normal", className)}
			{...props}
		/>
	);
}

export { Alert, AlertIcon, AlertTitle, AlertDescription, alertVariants };
