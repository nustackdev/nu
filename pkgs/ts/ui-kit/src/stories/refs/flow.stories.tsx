// Refs/Flow: Row and Column as a program draws them. In a Row each child
// sizes by its kind: fill children (charts, cards, inputs) share the free
// width and wrap at the row's `min_width`, content children (buttons,
// badges, text) keep their size. A Divider stands vertical in a Row. In a
// stretch Column fill children span the width and content children keep it.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { chartSet, chartStep } from "./chart-samples";
import { NodeStage, sinkParameters, step } from "./harness";

const meta: Meta = {
	title: "Refs/Flow",
	parameters: sinkParameters,
};

export default meta;

type Story = StoryObj;

function card(segment: string, title: string, label: string, value: string, note: string) {
	return [
		[step(segment, "Card", { title, subtitle: "", caption: "" })],
		[step(segment, "Card"), step("stat", "StatRef", { label, value })],
		[step(segment, "Card"), step("note", "TextRef", { value: note })],
	];
}

export const WrappingCards: Story = {
	render: () => {
		const row = step("flow-cards", "Row", { gap: 4, wrap: true, align: "stretch", min_width: 200 });
		const under = (chains: ReturnType<typeof step>[][]) => chains.map((c) => [row, ...c]);
		return (
			<NodeStage
				root="flow-cards"
				label="Row(wrap=True, align='stretch') of four cards: several per line, equal heights"
				chains={[
					[row],
					...under(
						card("a", "Serengeti", "Lions", "1,240", "Counted across the plains this season."),
					),
					...under(card("b", "Yellowstone", "Elk", "7,020", "Herd after the wolves came back.")),
					...under(card("c", "Manchester", "Moths", "62%", "Dark morphs on sooty bark.")),
					...under(card("d", "Galapagos", "Finches", "18", "Species across the islands.")),
				]}
			/>
		);
	},
};

export const ChartBesideCard: Story = {
	render: () => {
		const row = step("flow-chart", "Row", { gap: 4 });
		return (
			<NodeStage
				root="flow-chart"
				label="a LineChart and a Card share the width, neither collapses"
				frames={[chartSet(["flow-chart", "trend"], "line-time")]}
				chains={[
					[row, chartStep("trend", "line-time")],
					[row, step("side", "Card", { title: "Yellowstone" })],
					[
						row,
						step("side", "Card"),
						step("t", "TextRef", { value: "Wolves off: elk climb to about 18k." }),
					],
				]}
			/>
		);
	},
};

export const PieAndBars: Story = {
	render: () => {
		const row = step("flow-pie", "Row", { gap: 4 });
		return (
			<NodeStage
				root="flow-pie"
				label="a donut PieChart beside a horizontal BarChart"
				chains={[
					[row, chartStep("pie", "donut")],
					[row, chartStep("bars", "bar-horizontal")],
				]}
				frames={[
					chartSet(["flow-pie", "pie"], "donut"),
					chartSet(["flow-pie", "bars"], "bar-horizontal"),
				]}
			/>
		);
	},
};

export const Toolbar: Story = {
	render: () => {
		const row = step("flow-toolbar", "Row", { gap: 2 });
		return (
			<NodeStage
				root="flow-toolbar"
				label="buttons keep their size, a Divider stands vertical, an input fills the rest"
				chains={[
					[row, step("run", "ButtonRef", { label: "Run" })],
					[row, step("stop", "ButtonRef", { label: "Stop", variant: "secondary" })],
					[row, step("sep", "DividerRef")],
					[row, step("q", "InputRef", { placeholder: "Filter species" })],
					[row, step("live", "BadgeRef", { label: "live", variant: "ok" })],
				]}
			/>
		);
	},
};

export const StretchColumn: Story = {
	render: () => {
		const col = step("flow-column", "Column", { gap: 3 });
		return (
			<NodeStage
				root="flow-column"
				label="a stretch Column: the input spans, the button and badge keep their width"
				chains={[
					[col, step("h", "HeadingRef", { label: "Log a sighting", level: 4 })],
					[col, step("q", "InputRef", { placeholder: "Species" })],
					[col, step("go", "ButtonRef", { label: "Log it" })],
					[col, step("b", "BadgeRef", { label: "synced", variant: "info" })],
				]}
			/>
		);
	},
};
