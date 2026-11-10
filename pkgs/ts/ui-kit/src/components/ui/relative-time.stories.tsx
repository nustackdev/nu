import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { RelativeTime, type RelativeTimeMode } from "./relative-time";

const S = 1_000;
const M = 60 * S;
const H = 60 * M;
const D = 24 * H;

// Offsets back from the moment the story mounts, one per magnitude.
const OFFSETS: [string, number][] = [
	["now", 0],
	["8 seconds", 8 * S],
	["52 seconds", 52 * S],
	["4 minutes", 4 * M + 10 * S],
	["59 minutes", 59 * M + 45 * S],
	["2 hours", 2 * H + 4 * M],
	["3 days", 3 * D + 5 * H],
	["2 months", 64 * D],
	["3 years", 3 * 366 * D],
];

function Caption({ children }: { children: string }) {
	return (
		<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
			{children}
		</div>
	);
}

function Column({ mode }: { mode: RelativeTimeMode }) {
	const [mounted] = useState(() => Date.now());
	return (
		<div>
			<Caption>{mode}</Caption>
			<div className="grid grid-cols-[8rem_auto] gap-x-6 gap-y-1.5 text-sm">
				{OFFSETS.map(([label, off]) => (
					<div key={label} className="contents">
						<span className="text-text-muted">{label}</span>
						<RelativeTime ts={mounted - off} mode={mode} className="text-text-primary" />
					</div>
				))}
			</div>
		</div>
	);
}

/** Both modes across magnitudes, live. Hover a value for the absolute time. */
export const Modes: StoryObj = {
	render: () => (
		<div className="flex flex-wrap gap-16 p-8">
			<Column mode="ago" />
			<Column mode="duration" />
		</div>
	),
};

/** In a row of text, as a list would use it: inherits size and color. */
export const Inline: StoryObj = {
	render: () => {
		const [mounted] = useState(() => Date.now());
		return (
			<div className="space-y-2 p-8 text-sm text-text-secondary">
				<p>
					deploy finished <RelativeTime ts={mounted - 40 * M} />
				</p>
				<p>
					worker up for{" "}
					<RelativeTime ts={mounted - 26 * H} mode="duration" className="text-text-primary" />
				</p>
				<p className="font-mono text-xs text-text-muted">
					job running <RelativeTime ts={mounted - 3 * M - 12 * S} mode="duration" />
				</p>
			</div>
		);
	},
};

/** A thousand stamps on one shared timer. */
export const Many: StoryObj = {
	render: () => {
		const [mounted] = useState(() => Date.now());
		return (
			<div className="grid grid-cols-[repeat(auto-fill,minmax(7rem,1fr))] gap-1 p-8 text-xs text-text-secondary">
				{Array.from({ length: 1000 }, (_, i) => (
					// biome-ignore lint/suspicious/noArrayIndexKey: a fixed list, never reordered
					<RelativeTime key={i} ts={mounted - i * i * 997} mode={i % 2 ? "duration" : "ago"} />
				))}
			</div>
		);
	},
};

/** A missing stamp. */
export const Missing: StoryObj = {
	render: () => (
		<div className="p-8 text-sm">
			<RelativeTime ts={Number.NaN} />
		</div>
	),
};

const meta: Meta = {
	title: "UI/RelativeTime",
};

export default meta;
