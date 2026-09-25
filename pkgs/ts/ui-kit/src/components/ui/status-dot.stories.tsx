import type { Meta, StoryObj } from "@storybook/react-vite";
import { StatusDot } from "./status-dot";

const TONES = ["neutral", "info", "ok", "warn", "danger"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
			<StatusDot tone="ok" label="Running" />
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6">
			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					tones x pulse
				</div>
				<div className="space-y-3">
					{TONES.map((t) => (
						<div key={t} className="flex items-center gap-3">
							<div className="w-20 font-mono text-xs text-text-muted">{t}</div>
							<StatusDot tone={t} label={t} />
							<StatusDot tone={t} pulse label={t} />
						</div>
					))}
				</div>
			</div>

			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					beside its words
				</div>
				<div className="flex items-center gap-2 text-sm text-text-secondary">
					<StatusDot tone="ok" />
					Connected
				</div>
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/StatusDot",
};

export default meta;
