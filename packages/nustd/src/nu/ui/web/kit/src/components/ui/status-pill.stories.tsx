import type { Meta, StoryObj } from "@storybook/react-vite";
import { StatusPill } from "./status-pill";

const TONES = ["neutral", "info", "ok", "warn", "danger"] as const;
const SIZES = ["sm", "md"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<StatusPill tone="ok">Running</StatusPill>
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						tones x sizes
					</div>
					<div className="space-y-3">
						{TONES.map((t) => (
							<div key={t} className="flex items-center gap-3">
								<div className="w-20 font-mono text-xs text-text-muted">{t}</div>
								{SIZES.map((s) => (
									<StatusPill key={s} tone={t} size={s}>
										{t}
									</StatusPill>
								))}
							</div>
						))}
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/StatusPill",
};

export default meta;
