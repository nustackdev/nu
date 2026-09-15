import type { Meta, StoryObj } from "@storybook/react-vite";
import { Switch } from "./switch";

const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<Switch defaultChecked />
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						sizes
					</div>
					<div className="flex items-center gap-6">
						{SIZES.map((s) => (
							<div key={s} className="flex flex-col items-center gap-2">
								<Switch size={s} defaultChecked />
								<div className="font-mono text-xs text-text-muted">{s}</div>
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						states
					</div>
					<div className="flex flex-wrap items-center gap-6">
						<label className="flex items-center gap-2">
							<Switch />
							<span className="text-sm text-text-secondary">off</span>
						</label>
						<label className="flex items-center gap-2">
							<Switch defaultChecked />
							<span className="text-sm text-text-secondary">on</span>
						</label>
						<label className="flex items-center gap-2">
							<Switch disabled />
							<span className="text-sm text-text-secondary">disabled</span>
						</label>
						<label className="flex items-center gap-2">
							<Switch disabled defaultChecked />
							<span className="text-sm text-text-secondary">disabled on</span>
						</label>
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Switch",
};

export default meta;
