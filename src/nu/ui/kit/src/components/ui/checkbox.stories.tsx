import type { Meta, StoryObj } from "@storybook/react-vite";
import { Checkbox } from "./checkbox";

const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<Checkbox />
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
								<Checkbox size={s} defaultChecked />
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
							<Checkbox />
							<span className="text-sm text-text-secondary">unchecked</span>
						</label>
						<label className="flex items-center gap-2">
							<Checkbox defaultChecked />
							<span className="text-sm text-text-secondary">checked</span>
						</label>
						<label className="flex items-center gap-2">
							<Checkbox checked="indeterminate" />
							<span className="text-sm text-text-secondary">indeterminate</span>
						</label>
						<label className="flex items-center gap-2">
							<Checkbox disabled />
							<span className="text-sm text-text-secondary">disabled</span>
						</label>
						<label className="flex items-center gap-2">
							<Checkbox invalid />
							<span className="text-sm text-text-secondary">invalid</span>
						</label>
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Checkbox",
};

export default meta;
