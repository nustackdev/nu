import type { Meta, StoryObj } from "@storybook/react-vite";
import { Slider } from "./slider";

const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-md">
				<Slider defaultValue={[40]} />
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 max-w-md space-y-6">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						sizes
					</div>
					<div className="space-y-5">
						{SIZES.map((s) => (
							<div key={s}>
								<div className="mb-2 font-mono text-xs text-text-muted">{s}</div>
								<Slider size={s} defaultValue={[35]} />
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						states
					</div>
					<div className="space-y-4">
						<div>
							<div className="mb-2 font-mono text-xs text-text-muted">range</div>
							<Slider defaultValue={[20, 70]} />
						</div>
						<div>
							<div className="mb-2 font-mono text-xs text-text-muted">disabled</div>
							<Slider defaultValue={[40]} disabled />
						</div>
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Slider",
};

export default meta;
