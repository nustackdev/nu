import type { Meta, StoryObj } from "@storybook/react-vite";
import { ColorPicker } from "./color-picker";

const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
			<div className="w-44">
				<ColorPicker defaultValue="#8946db" swatches="palette" aria-label="Accent" />
			</div>
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-8">
			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					sizes
				</div>
				<div className="flex items-center gap-3">
					{SIZES.map((s) => (
						<div key={s} className="w-40">
							<ColorPicker size={s} defaultValue="#4269d0" aria-label={`Color ${s}`} />
						</div>
					))}
				</div>
			</div>

			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					states
				</div>
				<div className="flex items-center gap-3">
					<div className="w-40">
						<ColorPicker defaultValue="#3ca951" invalid aria-label="Invalid" />
					</div>
					<div className="w-40">
						<ColorPicker defaultValue="#3ca951" disabled aria-label="Disabled" />
					</div>
					<div className="w-24">
						<ColorPicker defaultValue="#f46853" showHex={false} aria-label="Swatch only" />
					</div>
				</div>
			</div>

			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					swatches
				</div>
				<div className="flex items-center gap-3">
					<div className="w-40">
						<ColorPicker defaultValue="#a463f2" swatches="palette" aria-label="Palette" />
					</div>
					<div className="w-40">
						<ColorPicker
							defaultValue="#111111"
							swatches={["#111111", "#555555", "#999999", "#dddddd", "#ffffff"]}
							aria-label="Greys"
						/>
					</div>
				</div>
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/ColorPicker",
};

export default meta;
