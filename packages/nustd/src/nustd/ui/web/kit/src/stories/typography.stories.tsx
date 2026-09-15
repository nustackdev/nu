// Typography visual reference. Scale, weights, both font families.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { Heading } from "../components/ui/heading";
import { Text } from "../components/ui/text";

const SAMPLE = "The quick brown fox jumps over the lazy dog";

const SCALE: Array<{
	name: string;
	twClass: string;
	rem: string;
	line: string;
}> = [
	{ name: "xs", twClass: "text-xs", rem: "0.6875rem / 11px", line: "1.45" },
	{ name: "sm", twClass: "text-sm", rem: "0.75rem / 12px", line: "1.4" },
	{ name: "base", twClass: "text-base", rem: "0.8125rem / 13px", line: "1.5" },
	{ name: "lg", twClass: "text-lg", rem: "0.875rem / 14px", line: "1.45" },
	{ name: "xl", twClass: "text-xl", rem: "1rem / 16px", line: "1.55" },
	{ name: "2xl", twClass: "text-2xl", rem: "1.25rem / 20px", line: "1.4" },
	{ name: "3xl", twClass: "text-3xl", rem: "1.5rem / 24px", line: "1.3" },
	{ name: "display", twClass: "text-display", rem: "2rem / 32px", line: "1.2" },
];

const WEIGHTS: Array<{ name: string; value: string; twClass: string }> = [
	{ name: "regular", value: "400", twClass: "font-normal" },
	{ name: "medium", value: "500", twClass: "font-medium" },
	{ name: "semibold", value: "600", twClass: "font-semibold" },
	{ name: "bold", value: "700", twClass: "font-bold" },
];

export const Scale: StoryObj = {
	render: () => (
		<div className="mx-auto max-w-5xl px-8 py-12">
				<Heading as="h1" size="3xl" className="mb-2">
					Type scale
				</Heading>
				<Text size="sm" tone="secondary" className="mb-10">
					Eight-step ladder. Inter for display and UI; JetBrains Mono for code and
					readouts.
				</Text>

				<div className="space-y-8">
					{SCALE.map((step) => (
						<div key={step.name} className="grid grid-cols-1 gap-2 md:grid-cols-[8rem_1fr_10rem]">
							<div className="space-y-0.5">
								<div className="font-mono text-xs text-text-primary">{step.name}</div>
								<div className="font-mono text-[10.5px] text-text-muted">
									{step.rem}
								</div>
								<div className="font-mono text-[10.5px] text-text-muted">
									line {step.line}
								</div>
							</div>
							<div className={`font-display text-text-primary ${step.twClass}`}>
								{SAMPLE}
							</div>
							<div className={`font-mono text-text-secondary ${step.twClass}`}>
								{SAMPLE.slice(0, 20)}...
							</div>
						</div>
					))}
				</div>
			</div>
	),
};

export const Weights: StoryObj = {
	render: () => (
		<div className="mx-auto max-w-5xl px-8 py-12">
				<Heading as="h1" size="3xl" className="mb-2">
					Weight scale
				</Heading>
				<Text size="sm" tone="secondary" className="mb-10">
					Four weights. Loaded per family from self-hosted WOFF2.
				</Text>

				<div className="grid grid-cols-1 gap-8 md:grid-cols-2">
					<div>
						<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
							Inter (display)
						</div>
						<div className="space-y-3">
							{WEIGHTS.map((w) => (
								<div key={w.name} className="grid grid-cols-[8rem_1fr] items-baseline gap-2">
									<span className="font-mono text-xs text-text-muted">
										{w.name} / {w.value}
									</span>
									<span className={`font-display text-xl text-text-primary ${w.twClass}`}>
										{SAMPLE}
									</span>
								</div>
							))}
						</div>
					</div>
					<div>
						<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
							JetBrains Mono (code)
						</div>
						<div className="space-y-3">
							{WEIGHTS.map((w) => (
								<div key={w.name} className="grid grid-cols-[8rem_1fr] items-baseline gap-2">
									<span className="font-mono text-xs text-text-muted">
										{w.name} / {w.value}
									</span>
									<span className={`font-mono text-xl text-text-primary ${w.twClass}`}>
										{SAMPLE}
									</span>
								</div>
							))}
						</div>
					</div>
				</div>
			</div>
	),
};

export const Families: StoryObj = {
	render: () => (
		<div className="mx-auto max-w-5xl px-8 py-12">
				<Heading as="h1" size="3xl" className="mb-2">
					Font families
				</Heading>
				<Text size="sm" tone="secondary" className="mb-10">
					Both families self-hosted as WOFF2 under kit/src/fonts/. Consumers get
					them for free by importing the kit styles.
				</Text>

				<div className="grid grid-cols-1 gap-8 md:grid-cols-2">
					<div>
						<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
							Inter
						</div>
						<div className="font-display text-3xl text-text-primary">
							Nu UI Kit
						</div>
						<div className="mt-2 font-display text-base text-text-secondary">
							Display, UI labels, form values, table cells.
						</div>
						<div className="mt-4 font-display text-sm text-text-muted">
							Contextual alternates, tabular numerals, kern.
						</div>
					</div>
					<div>
						<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
							JetBrains Mono
						</div>
						<div className="font-mono text-3xl text-text-primary">
							const kit = "nu"
						</div>
						<div className="mt-2 font-mono text-base text-text-secondary">
							Code, kbd chips, tick labels, id columns.
						</div>
						<div className="mt-4 font-mono text-sm text-text-muted">
							0O1lI iIl1 // legibility with dense punctuation
						</div>
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "Docs/Typography",
};

export default meta;
