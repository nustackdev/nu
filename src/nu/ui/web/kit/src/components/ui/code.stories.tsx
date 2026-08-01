import type { Meta, StoryObj } from "@storybook/react-vite";
import { Code } from "./code";

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				Inline: <Code>const x = 42</Code>
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 max-w-2xl space-y-6">
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						inline
					</div>
					<p className="text-sm text-text-primary">
						Reach for <Code>useState</Code> when a single value drives the surface;
						<Code>useReducer</Code> when transitions matter.
					</p>
				</div>

				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						block
					</div>
					<Code block language="tsx">
						{`import { Button } from "@nustackdev/ui-kit";

		export function Save() {
		  return <Button>Save</Button>;
		}`}
					</Code>
				</div>

				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						block + copyable
					</div>
					<Code block copyable language="sh">
						{`npm install @nustackdev/ui-kit`}
					</Code>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Code",
};

export default meta;
