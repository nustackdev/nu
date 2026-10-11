// Nodes/Line: the Line node as a program draws it. One sentence mixing a
// text run, a link, a badge, a shortcut and a status dot, wrapping like a
// paragraph; then the same Badge in a Column, a Row and a Line, where the
// parent's flow decides how it draws.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { NodeStage, sinkParameters, step } from "./harness";

const meta: Meta = {
	title: "Nodes/Line",
	parameters: sinkParameters,
};

export default meta;

type Story = StoryObj;

export const Sentence: Story = {
	render: () => {
		const line = step("line-sentence", "Line");
		return (
			<NodeStage
				root="line-sentence"
				label="text, link, badge, shortcut and status dot in one Line"
				chains={[
					[line, step("lead", "TextRef", { value: "Built with" })],
					[line, step("nu", "LinkRef", { href: "https://nustack.dev", label: "Nu" })],
					[line, step("ver", "BadgeRef", { label: "0.6", variant: "info" })],
					[line, step("mid", "TextRef", { value: "and ready: press" })],
					[line, step("keys", "ShortcutRef", { keys: ["mod", "K"] })],
					[line, step("tail", "TextRef", { value: "to search, status" })],
					[line, step("dot", "StatusDotRef", { tone: "ok", label: "live" })],
					[line, step("end", "TextRef", { value: "live." })],
				]}
			/>
		);
	},
};

export const Wrapping: Story = {
	render: () => {
		const line = step("line-wrap", "Line");
		return (
			<NodeStage
				root="line-wrap"
				label="a long run wraps mid-run beside the chips"
				chains={[
					[line, step("dot", "StatusDotRef", { tone: "warn", label: "degraded" })],
					[line, step("b", "BadgeRef", { label: "degraded", variant: "warn" })],
					[
						line,
						step("t", "TextRef", {
							value:
								"the plane keeps every write it has seen since the last snapshot and replays them in order when it comes back, so nothing a reader saw goes missing; press",
						}),
					],
					[line, step("k", "KbdRef", { label: "Esc" })],
					[line, step("t2", "TextRef", { value: "to dismiss." })],
				]}
			/>
		);
	},
};

export const SameBadgeThreeFlows: Story = {
	render: () => {
		const page = step("line-flows", "Column", { gap: 4 });
		const badge = { label: "0.6", variant: "info" };
		return (
			<NodeStage
				root="line-flows"
				label="the same Badge in a Column, a Row and a Line"
				chains={[
					[page, step("col", "Column", { gap: 2 }), step("t", "TextRef", { value: "In a Column" })],
					[page, step("col", "Column"), step("b", "BadgeRef", badge)],
					[page, step("row", "Row", { gap: 2 }), step("t", "TextRef", { value: "In a Row" })],
					[page, step("row", "Row"), step("b", "BadgeRef", badge)],
					[page, step("line", "Line"), step("t", "TextRef", { value: "In a Line" })],
					[page, step("line", "Line"), step("b", "BadgeRef", badge)],
					[page, step("line", "Line"), step("t2", "TextRef", { value: "it reads as a word." })],
				]}
			/>
		);
	},
};
