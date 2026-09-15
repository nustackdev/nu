import type { Meta, StoryObj } from "@storybook/react-vite";
import { Progress } from "./progress";

const TONES = ["default", "info", "ok", "warn", "danger"] as const;
const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-md">
				<Progress value={60} />
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
					<div className="space-y-4">
						{SIZES.map((s) => (
							<div key={s}>
								<div className="mb-1 font-mono text-xs text-text-muted">{s}</div>
								<Progress size={s} value={55} />
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						tones
					</div>
					<div className="space-y-4">
						{TONES.map((t) => (
							<div key={t}>
								<div className="mb-1 font-mono text-xs text-text-muted">{t}</div>
								<Progress tone={t} value={60} />
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
							<div className="mb-1 font-mono text-xs text-text-muted">0%</div>
							<Progress value={0} />
						</div>
						<div>
							<div className="mb-1 font-mono text-xs text-text-muted">100%</div>
							<Progress value={100} tone="ok" />
						</div>
						<div>
							<div className="mb-1 font-mono text-xs text-text-muted">indeterminate</div>
							<Progress value={null} />
						</div>
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Progress",
};

export default meta;
