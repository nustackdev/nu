import type { Meta, StoryObj } from "@storybook/react-vite";
import {
	Activity,
	ArrowRight,
	Bot,
	ChartLine,
	Clock,
	Database,
	FlaskConical,
	Layers,
	Package,
	Rocket,
	Server,
	Store,
	Terminal,
} from "lucide-react";
import { Button } from "./button";
import {
	Timeline,
	type TimelineItem,
	type TimelineLane,
	TimelineLegend,
	type TimelineTone,
} from "./timeline";

// A fixed "now", so every story draws the same each time.
const M = 60_000;
const H = 60 * M;
const D = 24 * H;
const END = Date.UTC(2026, 10, 10, 14, 0);

const NAMES = { ok: "done", danger: "failed", warn: "cancelled", neutral: "stopped" } as const;

type Span = [number, number | null, TimelineTone];

/** Intervals as [minutes ago start, minutes ago end (null: no end), tone]. */
function spans(list: Span[]): TimelineItem[] {
	return list.map(([a, b, tone], i) => ({
		start: END - a * M,
		end: b === null ? null : END - b * M,
		tone,
		label: `#${100 + i}`,
	}));
}

/** One interval every `step` ms over the last `span`, each `len` long, a few danger. */
function every(span: number, step: number, len: number, danger: number[] = []): TimelineItem[] {
	const n = Math.floor(span / step);
	return Array.from({ length: n }, (_, i) => {
		const start = END - span + i * step;
		return {
			start,
			end: start + len,
			tone: danger.includes(i) ? "danger" : "ok",
			label: `#${i + 1}`,
		};
	});
}

const lane = (
	id: string,
	icon: TimelineLane["icon"],
	title: string,
	items: TimelineItem[],
	count?: number,
): TimelineLane => ({ id, icon, title, href: `#/${id}`, items, count });

function Section({
	title,
	sub,
	children,
}: {
	title: string;
	sub: string;
	children: React.ReactNode;
}) {
	return (
		<div className="max-w-5xl p-8">
			<div className="mb-3 flex items-baseline gap-3">
				<h3 className="text-base font-semibold text-text-primary">{title}</h3>
				<span className="text-sm text-text-muted">{sub}</span>
			</div>
			{children}
		</div>
	);
}

const allLink = (
	<Button variant="ghost" size="sm" asChild>
		<a href="#/all">
			All
			<ArrowRight />
		</a>
	</Button>
);

const TYPICAL: TimelineLane[] = [
	lane("logs", Terminal, "Logs", spans([[60, null, "ok"]])),
	lane(
		"deploys",
		Rocket,
		"Deploys",
		spans([
			[58, 51, "ok"],
			[33, 31, "ok"],
			[12, 9, "danger"],
			[9, 6, "danger"],
			[4, null, "ok"],
		]),
	),
	lane(
		"imports",
		Store,
		"Imports",
		spans([
			[57, 56, "ok"],
			[42, 41, "ok"],
			[27, 26, "ok"],
			[18, 17.4, "danger"],
		]),
	),
	lane(
		"reports",
		ChartLine,
		"Reports",
		spans([
			[50, 38, "neutral"],
			[12, null, "ok"],
		]),
	),
	lane(
		"training",
		FlaskConical,
		"Training",
		spans([
			[60, 52, "warn"],
			[41, null, "ok"],
		]),
	),
	lane("chat", Bot, "Chat", spans([[60, null, "ok"]])),
];

/** A small team over the last hour: six lanes, a handful of intervals, no cap hit. */
export const Typical: StoryObj = {
	render: () => (
		<Section title="Last hour" sub="6 lanes · 15 jobs">
			<Timeline
				start={END - H}
				end={END}
				lanes={TYPICAL}
				noun="job"
				legend={NAMES}
				moreLabel="more lanes"
				more={allLink}
			/>
		</Section>
	),
};

const POWER: TimelineLane[] = [
	lane(
		"sweep",
		Layers,
		"shard sweep",
		// Twelve at once: three sub-rows, stacked, darker where they pile up.
		Array.from({ length: 12 }, (_, i) => ({
			start: END - (47 - i * 2) * M,
			end: i % 4 === 0 ? null : END - (20 - i) * M,
			tone: i === 5 ? "danger" : "ok",
			label: `shard ${i}`,
		})),
	),
	// A short job every 30s: 120 sent, 100 drawn, the full count on the right.
	lane("tick", Clock, "tick", every(H, 30_000, 2_000, [17, 64, 99]), 48_210),
	lane(
		"fetchers",
		Server,
		"Fetchers",
		spans([
			[60, 44, "danger"],
			[50, 30, "ok"],
			[43.5, null, "ok"],
		]),
	),
	lane("db", Database, "Backups", spans([[22, null, "ok"]])),
	// The host read only a page: it knows a lower bound, and says so.
	{
		...lane("sweep", Layers, "sweep", every(H, 40_000, 9_000, [3])),
		count: 100,
		countLabel: "100+ jobs",
	},
	lane("nightly", Package, "nightly", every(H, 5 * M, 3 * M, [4])),
	lane("logs", Terminal, "Logs", spans([[60, null, "ok"]])),
	lane("imports", Store, "Imports", every(H, 12 * M, 40_000, [2])),
	lane(
		"deploys",
		Rocket,
		"Deploys",
		spans([
			[58, 51, "ok"],
			[33, 31, "ok"],
			[12, 9, "danger"],
			[4, null, "ok"],
		]),
	),
	lane("chat", Bot, "Chat", spans([[60, null, "ok"]])),
	lane("reports", ChartLine, "Reports", spans([[30, 29, "ok"]])),
	lane("models", FlaskConical, "Models", spans([[30, 29, "ok"]])),
];

/** Caps hit: 10 of 2,150 lanes drawn, a lane past 100 items, twelve overlapping in one lane. */
export const Power: StoryObj = {
	render: () => (
		<Section title="Last hour" sub="2,150 lanes · 48.2K jobs">
			<Timeline
				start={END - H}
				end={END}
				lanes={POWER}
				totalLanes={2150}
				noun="job"
				legend={NAMES}
				moreLabel="more lanes"
				more={allLink}
			/>
		</Section>
	),
};

/** A short window: the last 10 minutes, jobs a second or two long drawn at the minimum width. */
export const ShortSpan: StoryObj = {
	render: () => (
		<Section title="Last 10 minutes" sub="3 lanes">
			<Timeline
				start={END - 10 * M}
				end={END}
				maxLanes={0}
				noun="job"
				legend={NAMES}
				lanes={[
					lane("tick", Clock, "tick", every(10 * M, 15_000, 1_500, [9, 30])),
					lane(
						"deploys",
						Rocket,
						"Deploys",
						spans([
							[8, 6.5, "ok"],
							[3, 2.2, "danger"],
							[1, null, "ok"],
						]),
					),
					lane("chat", Bot, "Chat", spans([[10, null, "ok"]])),
				]}
			/>
		</Section>
	),
};

const RECENT: TimelineLane[] = [
	lane("deploys", Rocket, "Deploys", [
		...every(3 * D, 6 * H, 20 * M, [4]),
		{ start: END - 20 * M, end: null, tone: "ok" },
	]),
	lane("tick", Clock, "tick", every(3 * D, 45 * M, 2 * M, [20, 70]), 5_760),
	lane("imports", Store, "Imports", every(3 * D, 12 * H, 50 * M)),
	lane("reports", ChartLine, "Reports", [
		{ start: END - 2.5 * D, end: END - 2.1 * D, tone: "neutral" },
	]),
	lane("training", FlaskConical, "Training", [
		{ start: END - 1.5 * D, end: END - 0.9 * D, tone: "warn" },
		{ start: END - 1.2 * D, end: END - 0.6 * D, tone: "ok" },
		{ start: END - 0.5 * D, end: null, tone: "ok" },
	]),
	lane("nightly", Package, "nightly", every(3 * D, D, 2 * H)),
	lane("activity", Activity, "Activity", every(3 * D, 3 * H, 90 * M, [3, 11])),
];

/** A multi-day window: lanes the caller picked, all drawn, no more row, a note under them. */
export const MultiDay: StoryObj = {
	render: () => (
		<Section title="Recent" sub="7 lanes">
			<Timeline
				start={END - 3 * D}
				end={END}
				lanes={RECENT}
				maxLanes={0}
				noun="job"
				legend={NAMES}
				note="The lanes that ran last, newest first."
			/>
		</Section>
	),
};

// One job an hour over a day, two of them failed.
const DAILY = every(D, H, 25 * M, [7, 19]);

/** Wall clock ticks over a day, an emoji mark, no legend: the tones go unnamed. */
export const ClockAxis: StoryObj = {
	render: () => (
		<Section title="Today" sub="clock axis">
			<Timeline
				start={END - D}
				end={END}
				axis="clock"
				lanes={[
					{ title: "Hourly sync", icon: Activity, items: DAILY },
					{ title: "Alerts", mark: "🔔", items: [] },
				]}
			/>
		</Section>
	),
};

/** The legend on its own, for a host that puts it in its section header. */
export const Legend: StoryObj = {
	render: () => (
		<div className="p-8">
			<TimelineLegend names={{ ...NAMES, info: "queued" }} />
		</div>
	),
};

const meta: Meta = {
	title: "UI/Timeline",
};

export default meta;
