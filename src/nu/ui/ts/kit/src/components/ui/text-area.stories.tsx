import type { Meta, StoryObj } from "@storybook/react-vite";
import { TextArea } from "./text-area";

const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-xl">
				<TextArea placeholder="Write a description..." />
			</div>
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
							<div key={s}>
								<div className="mb-1 font-mono text-xs text-text-muted">{s}</div>
								<TextArea size={s} placeholder={`Size ${s}`} />
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						states
					</div>
					<div className="space-y-3">
						<TextArea defaultValue="With value" />
						<TextArea disabled placeholder="Disabled" />
						<TextArea invalid defaultValue="invalid input" />
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/TextArea",
};

export default meta;
