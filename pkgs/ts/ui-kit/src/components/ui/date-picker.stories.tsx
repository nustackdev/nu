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
						<div className="w-56">
							<DatePicker clearable defaultValue={new Date(2016, 10, 11)} />
						</div>
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						range
					</div>
					<div className="flex gap-3">
						<div className="w-72">
							<DateRangePicker />
						</div>
						<div className="w-72">
							<DateRangePicker
								clearable
								defaultValue={{ from: new Date(2016, 10, 11), to: new Date(2016, 10, 13) }}
							/>
						</div>
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/DatePicker",
};

export default meta;
