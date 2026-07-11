import type { Meta, StoryObj } from "@storybook/react-vite";
import { Sparkline } from "./sparkline";

const SERIES_A = Array.from({ length: 24 }, (_, i) =>
	Math.round(50 + Math.sin(i * 0.6) * 20 + i * 0.5),
);
const SERIES_B = Array.from({ length: 24 }, (_, i) =>
	Math.round(60 + Math.cos(i * 0.4) * 15),
);

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 w-40">
				<Sparkline data={SERIES_A} />
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6 max-w-md">
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						default (h 24)
					</div>
					<div className="w-40">
						<Sparkline data={SERIES_A} />
					</div>
				</div>
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						taller (h 40)
					</div>
					<div className="w-40">
						<Sparkline data={SERIES_A} height={40} />
					</div>
				</div>
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						with dots + tooltip
					</div>
					<div className="w-40">
						<Sparkline data={SERIES_B} showDots showTooltip />
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Sparkline",
};

export default meta;
