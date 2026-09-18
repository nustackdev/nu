import type { Meta, StoryObj } from "@storybook/react-vite";
import { Separator } from "./separator";

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-md">
				<div className="text-sm text-text-primary">Above the line.</div>
				<Separator className="my-3" />
				<div className="text-sm text-text-primary">Below the line.</div>
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-8 max-w-lg">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						horizontal
					</div>
					<div className="space-y-3">
						<div className="text-sm text-text-primary">Row A</div>
						<Separator />
						<div className="text-sm text-text-primary">Row B</div>
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						vertical
					</div>
					<div className="flex h-8 items-center gap-3">
						<span className="text-sm text-text-primary">Left</span>
						<Separator orientation="vertical" />
						<span className="text-sm text-text-primary">Middle</span>
						<Separator orientation="vertical" />
						<span className="text-sm text-text-primary">Right</span>
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						labeled
					</div>
					<Separator label="or continue with" />
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Separator",
};

export default meta;
