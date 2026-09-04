import type { Meta, StoryObj } from "@storybook/react-vite";
import { JsonView } from "./json-view";

const SAMPLE = {
	run: "run_142",
	model: "gpt-5",
	tokens: {
		input: 843,
		output: 441,
		total: 1284,
	},
	tools: ["search", "eval", "publish"],
	status: "ok",
	nested: {
		deep: {
			depth: 3,
			leaf: true,
		},
	},
};

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-2xl">
				<JsonView value={SAMPLE} />
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 max-w-2xl space-y-6">
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						default (interactive)
					</div>
					<JsonView value={SAMPLE} />
				</div>
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						collapse depth = 1
					</div>
					<JsonView value={SAMPLE} collapsed={1} />
				</div>
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						collapse all
					</div>
					<JsonView value={SAMPLE} collapseAll />
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/JsonView",
};

export default meta;
