// Kitchen sink: the Grid primitive at every column count, the auto fit, the
// gap ladder and both alignments, light and dark side by side.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Grid, type GridAlign } from "../../components/ui/grid";
import { Stat, StatDelta, StatLabel, StatValue } from "../../components/ui/stat";
import { Text } from "../../components/ui/text";
import { Block, Row, SinkPage, sinkParameters, ThemePair } from "./frame";

const COUNTS = [1, 2, 3, 4] as const;
const GAPS = [1, 2, 3, 4, 6] as const;
const ALIGNS: GridAlign[] = ["stretch", "start", "center", "end"];

function Cell({ n }: { n: number }) {
	return (
		<Card variant="sunken">
			<CardContent className="py-2">
				<Text size="xs" tone="secondary" mono>
					{n}
				</Text>
			</CardContent>
		</Card>
	);
}

function cells(count: number) {
	return Array.from({ length: count }, (_, i) => <Cell key={i} n={i + 1} />);
}

function Grids() {
	return (
		<>
			<Block title="Columns">
				{COUNTS.map((n) => (
					<Row key={n} label={`columns ${n}`}>
						<Grid className="w-full" columns={n} minWidth={64} gap={3}>
							{cells(n * 2)}
						</Grid>
					</Row>
				))}
				<Row label="columns 0, 96px">
					<Grid className="w-full" minWidth={96} gap={3}>
						{cells(9)}
					</Grid>
				</Row>
				<Row label="columns 3, 240px">
					<Grid className="w-full" columns={3} minWidth={240} gap={3}>
						{cells(3)}
					</Grid>
				</Row>
			</Block>
			<Block title="Gap">
				{GAPS.map((gap) => (
					<Row key={gap} label={`gap ${gap} (${gap * 4}px)`}>
						<Grid className="w-full" columns={4} minWidth={48} gap={gap}>
							{cells(4)}
						</Grid>
					</Row>
				))}
			</Block>
			<Block title="Align">
				{ALIGNS.map((align) => (
					<Row key={align} label={align}>
						<Grid className="w-full" columns={3} minWidth={96} gap={3} align={align}>
							<Cell n={1} />
							<Card variant="sunken">
								<CardContent className="py-2">
									<Text size="xs" tone="secondary" mono>
										2, three lines
										<br />
										of text
										<br />
										sets the row
									</Text>
								</CardContent>
							</Card>
							<Cell n={3} />
						</Grid>
					</Row>
				))}
			</Block>
			<Block title="Stat cards">
				<Row label="columns 2">
					<Grid className="w-full" columns={2} minWidth={160} gap={4}>
						<Card>
							<CardHeader>
								<CardTitle>Runs</CardTitle>
							</CardHeader>
							<CardContent className="pb-4">
								<Stat>
									<StatLabel>today</StatLabel>
									<StatValue>1,284</StatValue>
									<StatDelta direction="up">+ 12.4%</StatDelta>
								</Stat>
							</CardContent>
						</Card>
						<Card>
							<CardHeader>
								<CardTitle>Errors</CardTitle>
							</CardHeader>
							<CardContent className="pb-4">
								<Stat>
									<StatLabel>today</StatLabel>
									<StatValue>0.9%</StatValue>
									<StatDelta direction="down" invert>
										- 0.2 pp
									</StatDelta>
								</Stat>
							</CardContent>
						</Card>
					</Grid>
				</Row>
			</Block>
		</>
	);
}

export const Default: StoryObj = {
	name: "Grid",
	render: () => (
		<SinkPage
			title="Grid"
			description="Equal cells, row after row: column caps, the auto fit, gaps and alignment."
		>
			<ThemePair>
				<Grids />
			</ThemePair>
		</SinkPage>
	),
};

const meta: Meta = {
	title: "Kitchen Sink/Layout/Grid",
	parameters: sinkParameters,
};

export default meta;
