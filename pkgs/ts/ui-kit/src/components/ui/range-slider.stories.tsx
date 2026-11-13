import type { Meta, StoryObj } from "@storybook/react-vite";
import { RangeSlider } from "./range-slider";

const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-md">
			<RangeSlider defaultValue={[20, 70]} aria-label="Price" />
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
							<RangeSlider size={s} defaultValue={[25, 60]} aria-label={`Range ${s}`} />
						</div>
					))}
				</div>
			</div>

			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					states
				</div>
				<div className="space-y-5">
					<div>
						<div className="mb-2 font-mono text-xs text-text-muted">marks and format</div>
						<RangeSlider
							min={0}
							max={1}
							step={0.05}
							defaultValue={[0.2, 0.8]}
							marks={[{ value: 0 }, { value: 0.5, label: "half" }, { value: 1 }]}
							formatValue={(n) => `${Math.round(n * 100)}%`}
							aria-label="Share"
						/>
					</div>
					<div>
						<div className="mb-2 font-mono text-xs text-text-muted">no readout</div>
						<RangeSlider defaultValue={[10, 40]} showValue={false} aria-label="Window" />
					</div>
					<div>
						<div className="mb-2 font-mono text-xs text-text-muted">disabled</div>
						<RangeSlider defaultValue={[30, 50]} disabled aria-label="Disabled" />
					</div>
				</div>
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/RangeSlider",
};

export default meta;
