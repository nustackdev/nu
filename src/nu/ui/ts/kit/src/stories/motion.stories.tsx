// Motion visual reference. Duration buckets + easing curves. Interactive
// samples toggle so timings read on the page.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { Heading } from "../components/ui/heading";
import { Text } from "../components/ui/text";
import { Button } from "../components/ui/button";
import { Alert, AlertDescription, AlertIcon, AlertTitle } from "../components/ui/alert";

const DURATIONS: Array<{ name: string; ms: string; use: string }> = [
	{
		name: "instant",
		ms: "0ms",
		use: "Checkbox/Radio flip. State snaps, no transition.",
	},
	{
		name: "fast",
		ms: "120ms",
		use: "Hover paints, focus rings, small color shifts.",
	},
	{
		name: "base",
		ms: "180ms",
		use: "Popover/Tooltip/Menu enter, tab indicators.",
	},
	{
		name: "slow",
		ms: "280ms",
		use: "Dialog/Sheet overlay + content.",
	},
];

const EASINGS: Array<{ name: string; cb: string; use: string }> = [
	{ name: "ease-out", cb: "(0.2, 0, 0, 1)", use: "Enter transitions" },
	{ name: "ease-in", cb: "(0.4, 0, 1, 1)", use: "Exit transitions" },
	{ name: "ease-in-out", cb: "(0.4, 0, 0.2, 1)", use: "Cross-fades, Tab indicator" },
	{ name: "linear", cb: "(0, 0, 1, 1)", use: "Progress, spinner rotation" },
];

function MotionDemo({
	label,
	durationClass,
	easingClass,
}: {
	label: string;
	durationClass: string;
	easingClass: string;
}) {
	const [on, setOn] = useState(false);
	return (
		<div className="flex items-center gap-3">
			<Button variant="secondary" size="sm" onClick={() => setOn((v) => !v)}>
				Toggle
			</Button>
			<div className="relative h-10 flex-1 overflow-hidden rounded-md border border-border-subtle bg-bg-sunken">
				<div
					className={`absolute top-1 left-1 size-8 rounded-sm bg-accent transition-transform ${durationClass} ${easingClass}`}
					style={{
						transform: on ? "translateX(calc(100% + 8rem))" : "translateX(0)",
					}}
				/>
			</div>
			<div className="w-40 font-mono text-xs text-text-muted">{label}</div>
		</div>
	);
}

export const Durations: StoryObj = {
	render: () => (
		<div className="mx-auto max-w-4xl px-8 py-12">
				<Heading as="h1" size="3xl" className="mb-2">
					Motion durations
				</Heading>
				<Text size="sm" tone="secondary" className="mb-10">
					Four buckets. Toggle each demo to see the timing. Kit reads {`prefers-reduced-motion`}
					{" "}and drops transition duration to 0.01ms.
				</Text>

				<div className="space-y-3">
					{DURATIONS.map((d) => (
						<div
							key={d.name}
							className="rounded-md border border-border-subtle bg-bg-surface p-4"
						>
							<div className="mb-3 flex items-baseline gap-3">
								<div className="font-mono text-sm text-text-primary">{d.name}</div>
								<div className="font-mono text-xs text-text-muted">{d.ms}</div>
							</div>
							<Text size="sm" tone="secondary" className="mb-3">
								{d.use}
							</Text>
							<MotionDemo
								label={`duration-${d.name}`}
								durationClass={`duration-${d.name}`}
								easingClass="ease-out"
							/>
						</div>
					))}
				</div>
			</div>
	),
};

export const Easings: StoryObj = {
	render: () => (
		<div className="mx-auto max-w-4xl px-8 py-12">
				<Heading as="h1" size="3xl" className="mb-2">
					Easing curves
				</Heading>
				<Text size="sm" tone="secondary" className="mb-10">
					One curve family, JetBrains-inspired. Enter uses ease-out, exit uses
					ease-in, cross-fades use ease-in-out, progress and spinners use linear.
				</Text>

				<div className="space-y-3">
					{EASINGS.map((e) => (
						<div
							key={e.name}
							className="rounded-md border border-border-subtle bg-bg-surface p-4"
						>
							<div className="mb-3 flex items-baseline gap-3">
								<div className="font-mono text-sm text-text-primary">{e.name}</div>
								<div className="font-mono text-xs text-text-muted">
									cubic-bezier{e.cb}
								</div>
							</div>
							<Text size="sm" tone="secondary" className="mb-3">
								{e.use}
							</Text>
							<MotionDemo
								label={`ease-${e.name.replace("ease-", "")} + duration-slow`}
								durationClass="duration-slow"
								easingClass={e.name === "linear" ? "ease-linear" : e.name}
							/>
						</div>
					))}
				</div>
			</div>
	),
};

export const ReducedMotion: StoryObj = {
	render: () => (
		<div className="mx-auto max-w-3xl px-8 py-12">
				<Heading as="h1" size="3xl" className="mb-2">
					Reduced motion
				</Heading>
				<Text size="sm" tone="secondary" className="mb-8">
					The kit clamps every transition + animation to 0.01ms when the OS
					preference is set. 0 would break Radix Presence (needs a transitionend
					event); 0.01ms fires the event but stays imperceptible.
				</Text>

				<Alert tone="info">
					<AlertIcon />
					<div>
						<AlertTitle>Toggle at the OS level to test</AlertTitle>
						<AlertDescription>
							macOS: System Settings, Accessibility, Display, Reduce motion. Linux:
							GNOME/KDE animations off. Windows: Settings, Ease of Access, Display,
							Show animations off.
						</AlertDescription>
					</div>
				</Alert>
			</div>
	),
};

const meta: Meta = {
	title: "Docs/Motion",
};

export default meta;
