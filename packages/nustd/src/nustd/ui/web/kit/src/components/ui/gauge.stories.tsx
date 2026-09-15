import type { Meta, StoryObj } from "@storybook/react-vite";
import { Gauge } from "./gauge";

const SIZES = ["sm", "md", "lg"] as const;
const TONES = ["accent", "info", "danger", "warn", "ok", "accent2"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<Gauge value={72} label="CPU" />
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
					<div className="flex items-end gap-6">
						{SIZES.map((s) => (
							<div key={s} className="flex flex-col items-center gap-2">
								<Gauge size={s} value={55} label={`${s} gauge`} />
								<div className="font-mono text-xs text-text-muted">{s}</div>
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						tones
					</div>
					<div className="flex flex-wrap items-end gap-6">
						{TONES.map((t) => (
							<div key={t} className="flex flex-col items-center gap-2">
								<Gauge tone={t} value={72} label={t} />
								<div className="font-mono text-xs text-text-muted">{t}</div>
							</div>
						))}
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Gauge",
};

export default meta;
