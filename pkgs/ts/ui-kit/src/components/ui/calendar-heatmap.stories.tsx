import type { Meta, StoryObj } from "@storybook/react-vite";
import { CalendarHeatmap } from "./calendar-heatmap";
import { type CalendarHeatmapValues, dayKey } from "./calendar-heatmap-model";

// Seeded so the stories never flicker. Two parts per day:
// jobs and builds finished.
function rng(seed: number) {
	let s = seed;
	return () => {
		s = (s * 16807) % 2147483647;
		return (s - 1) / 2147483646;
	};
}

interface Sample {
	born: Date;
	jobs: number;
	builds: number;
	jitter: number;
	gap: number;
	burst: number;
	seed: number;
	dip?: [Date, number];
}

const END = new Date(2026, 10, 10);

function sample(c: Sample): CalendarHeatmapValues {
	const r = rng(c.seed);
	const out: CalendarHeatmapValues = {};
	for (let i = 0; i < 380; i++) {
		const d = new Date(END.getFullYear(), END.getMonth(), END.getDate() - i);
		if (d < c.born) break;
		const weekend = d.getDay() === 0 || d.getDay() === 6;
		if (r() < c.gap * (weekend ? 1.3 : 1)) continue;
		const k = (weekend ? 0.35 : 1) * (r() < c.burst ? 3 + r() * 5 : 1);
		const j = () => 1 - c.jitter + r() * c.jitter * 2;
		let jobs = Math.max(0, Math.round(c.jobs * k * j()));
		let builds = Math.max(jobs, Math.round(c.builds * k * j()));
		if (c.dip) {
			const off = (d.getTime() - c.dip[0].getTime()) / 864e5;
			if (off >= 0 && off < c.dip[1]) {
				jobs = Math.round(jobs * 0.08);
				builds = Math.round(builds * 0.08);
			}
		}
		out[dayKey(d)] = { jobs, builds };
	}
	return out;
}

// A small team, started in May, quiet days and gaps.
const TYPICAL = sample({
	born: new Date(2026, 4, 18),
	jobs: 0.5,
	builds: 2.2,
	jitter: 0.9,
	gap: 0.8,
	burst: 0.06,
	seed: 7,
});

// A busy CI fleet: jobs in bulk, a full year, one outage.
const POWER = sample({
	born: new Date(2024, 1, 2),
	jobs: 30,
	builds: 2000,
	jitter: 0.6,
	gap: 0.03,
	burst: 0.08,
	seed: 17,
	dip: [new Date(2026, 6, 6), 9],
});

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
			<CalendarHeatmap values={TYPICAL} end={END} title="Finished per day" suffix="finished" />
		</div>
	),
};

export const Power: StoryObj = {
	render: () => (
		<div className="p-8">
			<CalendarHeatmap values={POWER} end={END} title="Finished per day" suffix="finished" />
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-8">
			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					plain counts, starlight, sunday first
				</div>
				<CalendarHeatmap
					values={Object.fromEntries(
						Object.entries(POWER).map(([k, v]) => [k, typeof v === "number" ? v : v.builds]),
					)}
					end={END}
					tone="accent-2"
					weekStart="sun"
					unit="commits"
					title="Commits per day"
				/>
			</div>
			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					empty, 26 weeks, bare
				</div>
				<CalendarHeatmap values={{}} end={END} weeks={26} showTotals={false} showLegend={false} />
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/CalendarHeatmap",
};

export default meta;
