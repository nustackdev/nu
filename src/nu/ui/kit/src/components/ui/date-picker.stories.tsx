import type { Meta, StoryObj } from "@storybook/react-vite";
import { DatePicker, DateRangePicker } from "./date-picker";

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<div className="w-56">
					<DatePicker />
				</div>
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-8">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						single
					</div>
					<div className="flex gap-3">
						<div className="w-56">
							<DatePicker />
						</div>
						<div className="w-56">
							<DatePicker invalid />
						</div>
						<div className="w-56">
							<DatePicker disabled />
						</div>
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						range
					</div>
					<div className="w-72">
						<DateRangePicker />
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/DatePicker",
};

export default meta;
