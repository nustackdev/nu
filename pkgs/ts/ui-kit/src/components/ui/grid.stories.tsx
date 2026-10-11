import type { Meta, StoryObj } from "@storybook/react-vite";
import { Card, CardContent, CardHeader, CardTitle } from "./card";
import { Grid } from "./grid";
import { Stat, StatDelta, StatLabel, StatValue } from "./stat";
import { Text } from "./text";

const STATS = [
	{ label: "Runs today", value: "1,284", delta: "+ 12.4%", direction: "up" },
	{ label: "Tokens spent", value: "842k", delta: "- 3.1%", direction: "down" },
	{ label: "Error rate", value: "0.9%", delta: "- 0.2 pp", direction: "down" },
	{ label: "Uptime", value: "99.94%", delta: "no change", direction: "flat" },
	{ label: "Queue depth", value: "37", delta: "+ 4", direction: "up" },
	{ label: "p95 latency", value: "182 ms", delta: "- 9 ms", direction: "down" },
] as const;

function StatCard({ i }: { i: number }) {
	const s = STATS[i % STATS.length];
	return (
		<Card>
			<CardContent className="py-3">
				<Stat>
					<StatLabel>{s.label}</StatLabel>
					<StatValue>{s.value}</StatValue>
					<StatDelta direction={s.direction}>{s.delta}</StatDelta>
				</Stat>
			</CardContent>
		</Card>
	);
}

function Tile({ n }: { n: number }) {
	return (
		<Card variant="sunken">
			<CardContent className="py-3">
				<Text size="sm" tone="secondary" mono>
					cell {n}
				</Text>
			</CardContent>
		</Card>
	);
}

/** Three columns at most: resize the canvas under 3 x 240px and it steps down, then stacks. */
export const Columns: StoryObj = {
	render: () => (
		<div className="p-8">
			<Grid columns={3}>
				{STATS.map((s, i) => (
					<StatCard key={s.label} i={i} />
				))}
			</Grid>
		</div>
	),
};

/** No cap: as many 160px columns as fit, every track the same width. */
export const AutoFit: StoryObj = {
	render: () => (
		<div className="p-8">
			<Grid minWidth={160} gap={3}>
				{Array.from({ length: 10 }, (_, i) => (
					<Tile key={i} n={i + 1} />
				))}
			</Grid>
		</div>
	),
};

/** Gap steps from the spacing ladder, tight to roomy. */
export const Gaps: StoryObj = {
	render: () => (
		<div className="flex flex-col gap-8 p-8">
			{[1, 2, 4, 6].map((gap) => (
				<div key={gap} className="flex flex-col gap-2">
					<Text size="xs" tone="muted" mono>
						gap {gap} ({gap * 4}px)
					</Text>
					<Grid columns={4} minWidth={120} gap={gap}>
						{[1, 2, 3, 4].map((n) => (
							<Tile key={n} n={n} />
						))}
					</Grid>
				</div>
			))}
		</div>
	),
};

/** Stretch (default) evens a row out to its tallest cell; start keeps each cell's own height. */
export const Align: StoryObj = {
	render: () => (
		<div className="flex flex-col gap-8 p-8">
			{(["stretch", "start"] as const).map((align) => (
				<div key={align} className="flex flex-col gap-2">
					<Text size="xs" tone="muted" mono>
						align {align}
					</Text>
					<Grid columns={3} minWidth={160} align={align}>
						<Card>
							<CardHeader>
								<CardTitle>Short</CardTitle>
							</CardHeader>
						</Card>
						<Card>
							<CardHeader>
								<CardTitle>Taller</CardTitle>
							</CardHeader>
							<CardContent className="pb-4">
								<Text size="sm" tone="secondary">
									Two lines of body text make this card the tallest one on the row.
								</Text>
							</CardContent>
						</Card>
						<Card>
							<CardHeader>
								<CardTitle>Short</CardTitle>
							</CardHeader>
						</Card>
					</Grid>
				</div>
			))}
		</div>
	),
};

const meta: Meta = {
	title: "UI/Grid",
};

export default meta;
