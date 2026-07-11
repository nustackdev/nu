// Spacing + radius visual reference.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { Heading } from "../components/ui/heading";
import { Text } from "../components/ui/text";

// Tailwind v4 default spacing scale (in 4px steps).
const SPACING: Array<{ name: string; px: string; twClass: string }> = [
	{ name: "0", px: "0px", twClass: "w-0" },
	{ name: "px", px: "1px", twClass: "w-px" },
	{ name: "0.5", px: "2px", twClass: "w-0.5" },
	{ name: "1", px: "4px", twClass: "w-1" },
	{ name: "1.5", px: "6px", twClass: "w-1.5" },
	{ name: "2", px: "8px", twClass: "w-2" },
	{ name: "3", px: "12px", twClass: "w-3" },
	{ name: "4", px: "16px", twClass: "w-4" },
	{ name: "5", px: "20px", twClass: "w-5" },
	{ name: "6", px: "24px", twClass: "w-6" },
	{ name: "8", px: "32px", twClass: "w-8" },
	{ name: "10", px: "40px", twClass: "w-10" },
	{ name: "12", px: "48px", twClass: "w-12" },
	{ name: "16", px: "64px", twClass: "w-16" },
	{ name: "20", px: "80px", twClass: "w-20" },
	{ name: "24", px: "96px", twClass: "w-24" },
];

const RADII: Array<{ name: string; value: string; twClass: string }> = [
	{ name: "none", value: "0", twClass: "rounded-none" },
	{ name: "sm", value: "4px", twClass: "rounded-sm" },
	{ name: "md", value: "6px", twClass: "rounded-md" },
	{ name: "lg", value: "8px", twClass: "rounded-lg" },
	{ name: "xl", value: "12px", twClass: "rounded-xl" },
	{ name: "2xl", value: "16px", twClass: "rounded-2xl" },
	{ name: "full", value: "9999px", twClass: "rounded-full" },
];

const CONTAINERS: Array<{ name: string; value: string; twClass: string }> = [
	{ name: "form", value: "480px", twClass: "container-form" },
	{ name: "prose", value: "640px", twClass: "container-prose" },
	{ name: "panel", value: "960px", twClass: "container-panel" },
	{ name: "dashboard", value: "1400px", twClass: "container-dashboard" },
];

export const Spacing: StoryObj = {
	render: () => (
		<div className="mx-auto max-w-5xl px-8 py-12">
				<Heading as="h1" size="3xl" className="mb-2">
					Spacing scale
				</Heading>
				<Text size="sm" tone="secondary" className="mb-10">
					4px base. Tailwind classes p-*, m-*, gap-*, w-*, h-* all key off this
					ladder. IDE density hits harder on the small end than shadcn defaults.
				</Text>

				<div className="space-y-2">
					{SPACING.map((s) => (
						<div
							key={s.name}
							className="grid grid-cols-[6rem_5rem_1fr] items-center gap-3"
						>
							<div className="font-mono text-xs text-text-primary">{s.name}</div>
							<div className="font-mono text-xs text-text-muted">{s.px}</div>
							<div className="flex items-center gap-2">
								<div className={`h-4 bg-accent rounded-sm ${s.twClass}`} />
							</div>
						</div>
					))}
				</div>
			</div>
	),
};

export const Radius: StoryObj = {
	render: () => (
		<div className="mx-auto max-w-5xl px-8 py-12">
				<Heading as="h1" size="3xl" className="mb-2">
					Radius scale
				</Heading>
				<Text size="sm" tone="secondary" className="mb-10">
					Card/Panel default to lg; Dialog/Sheet lg-xl; Input/Button md; Badge/Kbd
					sm; pill shapes full.
				</Text>

				<div className="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7">
					{RADII.map((r) => (
						<div key={r.name} className="flex flex-col items-center gap-2">
							<div
								className={`size-20 bg-accent-wash border border-accent-line ${r.twClass}`}
							/>
							<div className="text-center">
								<div className="font-mono text-xs text-text-primary">{r.name}</div>
								<div className="font-mono text-[10.5px] text-text-muted">{r.value}</div>
							</div>
						</div>
					))}
				</div>
			</div>
	),
};

export const Containers: StoryObj = {
	render: () => (
		<div className="mx-auto max-w-6xl px-8 py-12">
				<Heading as="h1" size="3xl" className="mb-2">
					Container widths
				</Heading>
				<Text size="sm" tone="secondary" className="mb-10">
					Max-width tokens for prose, form rails, panels, and dashboard shells.
				</Text>

				<div className="space-y-4">
					{CONTAINERS.map((c) => (
						<div key={c.name}>
							<div className="mb-1.5 flex items-baseline justify-between font-mono text-xs">
								<span className="text-text-primary">{c.name}</span>
								<span className="text-text-muted">{c.value}</span>
							</div>
							<div
								className="h-4 rounded-sm border border-border-subtle bg-accent-wash"
								style={{
									maxWidth: c.value,
								}}
							/>
						</div>
					))}
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "Docs/Space",
};

export default meta;
