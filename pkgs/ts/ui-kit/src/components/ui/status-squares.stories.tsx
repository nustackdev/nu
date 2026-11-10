import type { Meta, StoryObj } from "@storybook/react-vite";
import { type StatusSquareCounts, StatusSquares } from "./status-squares";

// Job states, worded per tone.
const JOB_LABELS = {
	danger: "failed",
	warn: "retrying",
	info: "starting",
	ok: "running",
	neutral: "stopped",
	empty: "idle",
} as const;

function Row({ name, counts }: { name: string; counts: StatusSquareCounts }) {
	return (
		<div className="flex items-center gap-4">
			<div className="w-32 truncate text-sm text-text-primary">{name}</div>
			<StatusSquares counts={counts} labels={JOB_LABELS} />
		</div>
	);
}

function Caption({ children }: { children: string }) {
	return (
		<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
			{children}
		</div>
	);
}

/** A small team: a few jobs per service, under the cap, no count needed. */
export const Typical: StoryObj = {
	render: () => (
		<div className="space-y-2 p-8">
			<Row name="orders" counts={{ ok: 4 }} />
			<Row name="billing" counts={{ ok: 3, info: 1 }} />
			<Row name="inventory" counts={{ ok: 5, danger: 1, empty: 1 }} />
			<Row name="mailer" counts={{ ok: 1, neutral: 1 }} />
			<Row name="reports" counts={{ warn: 1, ok: 2 }} />
		</div>
	),
};

/** A scripted fleet: caps hit, big counts, problems past the cap still drawn first. */
export const Power: StoryObj = {
	render: () => (
		<div className="space-y-2 p-8">
			<Row name="ingest-0001" counts={{ ok: 48 }} />
			<Row name="ingest-0002" counts={{ ok: 994, danger: 3, info: 2, neutral: 1 }} />
			<Row name="crawler" counts={{ ok: 12_431, danger: 17, warn: 4, empty: 220 }} />
			<Row name="batch-all" counts={{ danger: 14, info: 9, ok: 1_204_311 }} />
			<Row name="cold" counts={{ empty: 300, neutral: 40 }} />
		</div>
	),
};

export const Options: StoryObj = {
	render: () => (
		<div className="space-y-6 p-8">
			<div>
				<Caption>every tone, severity order</Caption>
				<StatusSquares counts={{ empty: 1, neutral: 1, ok: 1, info: 1, warn: 1, danger: 1 }} />
			</div>
			<div>
				<Caption>maxItems 5</Caption>
				<StatusSquares counts={{ ok: 30, danger: 2 }} maxItems={5} />
			</div>
			<div>
				<Caption>total always</Caption>
				<StatusSquares counts={{ ok: 3 }} total="always" />
			</div>
			<div>
				<Caption>total never (count in its own column)</Caption>
				<StatusSquares counts={{ ok: 300, danger: 1 }} total="never" />
			</div>
			<div>
				<Caption>empty</Caption>
				<StatusSquares counts={{}} total="always" />
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/StatusSquares",
};

export default meta;
