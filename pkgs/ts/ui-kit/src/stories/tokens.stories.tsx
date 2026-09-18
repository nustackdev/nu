// Token pages: L1 raw scales + L2 semantic role tokens.
// Swatches resolve computed color via getComputedStyle so both themes render
// their real hex under the current theme toggle.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { useEffect, useState } from "react";
import { Heading } from "../components/ui/heading";
import { Text } from "../components/ui/text";

const PRIMITIVES: Array<{ hue: string; steps: (string | number)[] }> = [
	{
		hue: "purple",
		steps: [25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950],
	},
	{
		hue: "blue",
		steps: [25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950],
	},
	{
		hue: "red",
		steps: [25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950],
	},
	{
		hue: "yellow",
		steps: [25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950],
	},
	{
		hue: "green",
		steps: [25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950],
	},
	{
		hue: "blue-info",
		steps: [25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950],
	},
	{
		hue: "gray",
		steps: [0, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
	},
];

const SEMANTIC: Array<{ group: string; vars: string[] }> = [
	{
		group: "surface",
		vars: ["--bg-canvas", "--bg-surface", "--bg-elevated", "--bg-sunken", "--bg-overlay"],
	},
	{
		group: "text",
		vars: ["--text-primary", "--text-secondary", "--text-muted", "--text-inverse"],
	},
	{
		group: "border",
		vars: ["--border-subtle", "--border-default", "--border-strong"],
	},
	{
		group: "accent (purple)",
		vars: ["--accent", "--accent-fg", "--accent-wash", "--accent-soft", "--accent-line", "--accent-hover"],
	},
	{
		group: "accent-2 (blue)",
		vars: [
			"--accent-2",
			"--accent-2-fg",
			"--accent-2-wash",
			"--accent-2-soft",
			"--accent-2-line",
			"--accent-2-hover",
		],
	},
	{
		group: "status danger",
		vars: ["--status-danger", "--status-danger-fg", "--status-danger-wash", "--status-danger-line"],
	},
	{
		group: "status warn",
		vars: ["--status-warn", "--status-warn-fg", "--status-warn-wash", "--status-warn-line"],
	},
	{
		group: "status ok",
		vars: ["--status-ok", "--status-ok-fg", "--status-ok-wash", "--status-ok-line"],
	},
	{
		group: "status info",
		vars: ["--status-info", "--status-info-fg", "--status-info-wash", "--status-info-line"],
	},
	{
		group: "chart categorical",
		vars: [
			"--chart-1",
			"--chart-2",
			"--chart-3",
			"--chart-4",
			"--chart-5",
			"--chart-6",
			"--chart-7",
			"--chart-8",
		],
	},
	{
		group: "focus",
		vars: ["--ring"],
	},
];

function useCssVarValue(name: string) {
	const [value, setValue] = useState("");
	useEffect(() => {
		function resolve() {
			try {
				setValue(getComputedStyle(document.documentElement).getPropertyValue(name).trim());
			} catch {
				setValue("");
			}
		}
		resolve();
		// Re-resolve when the theme toggles.
		const observer = new MutationObserver(resolve);
		observer.observe(document.documentElement, {
			attributes: true,
			attributeFilter: ["class"],
		});
		return () => observer.disconnect();
	}, [name]);
	return value;
}

function Swatch({ name, varName }: { name: string; varName: string }) {
	const value = useCssVarValue(varName);
	return (
		<div className="flex flex-col gap-1.5">
			<div
				className="h-14 rounded-md border border-border-subtle"
				style={{ background: `var(${varName})` }}
			/>
			<div className="space-y-0.5">
				<div className="text-xs font-medium text-text-primary">{name}</div>
				<div className="text-[10.5px] text-text-muted font-mono truncate" title={value}>
					{value || varName}
				</div>
			</div>
		</div>
	);
}

function Section({
	title,
	description,
	children,
}: {
	title: string;
	description?: string;
	children: React.ReactNode;
}) {
	return (
		<section className="border-t border-border-subtle py-10">
			<div className="mb-5 space-y-1">
				<Heading as="h2" size="xl">
					{title}
				</Heading>
				{description && (
					<Text size="sm" tone="secondary">
						{description}
					</Text>
				)}
			</div>
			{children}
		</section>
	);
}

export const Primitives: StoryObj = {
	render: () => (
		<div className="mx-auto max-w-6xl px-8 py-12">
				<div className="mb-10">
					<Heading as="h1" size="3xl" className="mb-2">
						L1 primitives
					</Heading>
					<Text size="sm" tone="secondary">
						Raw scales. Components must never reference these directly; they compose
						through L2 semantic roles.
					</Text>
				</div>
				<div className="space-y-10">
					{PRIMITIVES.map(({ hue, steps }) => (
						<div key={hue}>
							<div className="mb-3 flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-text-muted">
								<span>{hue}</span>
								<span className="text-text-muted">{steps.length} steps</span>
							</div>
							<div className="grid grid-cols-4 gap-3 md:grid-cols-6 lg:grid-cols-12">
								{steps.map((step) => (
									<Swatch
										key={step}
										name={`${hue}-${step}`}
										varName={`--${hue}-${step}`}
									/>
								))}
							</div>
						</div>
					))}
				</div>
			</div>
	),
};

export const Semantic: StoryObj = {
	render: () => (
		<div className="mx-auto max-w-6xl px-8 py-12">
				<div className="mb-10">
					<Heading as="h1" size="3xl" className="mb-2">
						L2 semantic tokens
					</Heading>
					<Text size="sm" tone="secondary">
						Role-named tokens. This is the API components consume. Theme toggle in
						the toolbar switches every value in one shot.
					</Text>
				</div>
				<div className="space-y-4">
					{SEMANTIC.map(({ group, vars }) => (
						<Section key={group} title={group}>
							<div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
								{vars.map((v) => (
									<Swatch key={v} name={v.replace(/^--/, "")} varName={v} />
								))}
							</div>
						</Section>
					))}
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "Docs/Tokens",
};

export default meta;
