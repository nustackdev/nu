import type { Meta, StoryObj } from "@storybook/react-vite";
import { Input } from "./input";

const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<Input placeholder="Search projects..." />
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 max-w-xl space-y-6">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						sizes
					</div>
					<div className="space-y-3">
						{SIZES.map((s) => (
							<div key={s} className="grid grid-cols-[4rem_1fr] items-center gap-3">
								<div className="font-mono text-xs text-text-muted">{s}</div>
								<Input size={s} placeholder={`Size ${s}`} />
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						states
					</div>
					<div className="space-y-3">
						<Input placeholder="Default" />
						<Input defaultValue="With value" />
						<Input disabled placeholder="Disabled" />
						<Input invalid defaultValue="invalid value" />
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Input",
};

export default meta;
