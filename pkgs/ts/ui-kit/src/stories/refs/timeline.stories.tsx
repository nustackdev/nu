// Refs/Timeline: TimelineRef as Python sends it. Lanes with lucide names
// and an emoji for icons, items as [start, end, tone, label] lists (end
// null: no end yet), more lanes than drawn, and a way to see them all.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { NodeStage, sinkParameters, step } from "./harness";

const meta: Meta = {
	title: "Refs/Timeline",
	parameters: sinkParameters,
};

export default meta;

type Story = StoryObj;

const M = 60_000;
const END = Date.UTC(2026, 10, 10, 14, 0);
const ago = (min: number) => END - min * M;

// A short job every 36 seconds, a few failed: 100 sent of 912.
const TICKS = Array.from({ length: 100 }, (_, i) => [
	ago(60) + i * 36_000,
	ago(60) + i * 36_000 + 2_000,
	i % 30 === 7 ? "danger" : "ok",
	`#${i + 1}`,
]);

export const LastHour: Story = {
	render: () => {
		const root = "timeline-last-hour";
		return (
			<NodeStage
				root={root}
				label="TimelineRef: 4 lanes sent of 2,150, an overlap, a lane past its cap, the more row"
				chains={[
					[
						step(root, "Column", { gap: 4 }),
						step("hour", "TimelineRef", {
							start: ago(60),
							end: END,
							noun: "job",
							legend: { ok: "done", danger: "failed", warn: "cancelled" },
							lanes: [
								{
									title: "Deploys",
									icon: "rocket",
									href: "#/deploys",
									items: [
										[ago(58), ago(51), "ok", "#12"],
										[ago(12), ago(9), "danger", "#13"],
										[ago(10), ago(2), "ok", "#14"],
										[ago(4), null, "ok", "#15"],
									],
								},
								{ title: "tick", icon: "clock", href: "#/tick", items: TICKS, count: 912 },
								{
									title: "Reports",
									icon: "📈",
									href: "#/reports",
									items: [
										[ago(50), ago(38), "warn"],
										[ago(12), null, "ok"],
									],
								},
								{ title: "Training", icon: "flask-conical", items: [[ago(60), ago(52), "warn"]] },
							],
							total_lanes: 2150,
							more_label: "more lanes",
							more_text: "All",
							more_href: "#/all",
							note: "Lanes with a job in the last hour.",
						}),
					],
				]}
			/>
		);
	},
};
