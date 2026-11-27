import type { Meta, StoryObj } from "@storybook/react-vite";
import { DateTimePicker, TimePicker } from "./time-picker";

const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 space-y-4">
			<div className="w-40">
				<TimePicker aria-label="Time" defaultValue="09:30" clearable />
			</div>
			<div className="w-96">
				<DateTimePicker aria-label="Starts" clearable />
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
				<div className="flex flex-wrap items-start gap-3">
					{SIZES.map((s) => (
						<div key={s} className="w-40">
							<TimePicker aria-label={`Time ${s}`} size={s} defaultValue="14:05" clearable />
						</div>
					))}
				</div>
			</div>

			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					states
				</div>
				<div className="flex flex-wrap items-start gap-3">
					<div className="w-40">
						<TimePicker aria-label="Empty" />
					</div>
					<div className="w-40">
						<TimePicker aria-label="Seconds" defaultValue="08:15:30" step={1} />
					</div>
					<div className="w-40">
						<TimePicker aria-label="Invalid" defaultValue="23:00" invalid />
					</div>
					<div className="w-40">
						<TimePicker aria-label="Readonly" defaultValue="12:00" readOnly clearable />
					</div>
					<div className="w-40">
						<TimePicker aria-label="Disabled" defaultValue="12:00" disabled />
					</div>
				</div>
			</div>

			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					date and time
				</div>
				<div className="space-y-3">
					{SIZES.map((s) => (
						<div key={s} className="w-full max-w-96">
							<DateTimePicker
								aria-label={`Starts ${s}`}
								size={s}
								defaultValue={new Date(2016, 10, 11, 19, 30)}
								clearable
							/>
						</div>
					))}
					<div className="w-full max-w-96">
						<DateTimePicker aria-label="Invalid" invalid />
					</div>
					<div className="w-full max-w-96">
						<DateTimePicker
							aria-label="Disabled"
							disabled
							defaultValue={new Date(2016, 10, 11, 19, 30)}
						/>
					</div>
				</div>
			</div>
		</div>
	),
};

// Opened at load: in touch mode the hour and minute columns in a bottom sheet
// with a Done button, on desktop the native time field focused.
export const Open: StoryObj = {
	render: () => (
		<div className="p-8">
			<div className="w-40">
				<TimePicker aria-label="Time" defaultValue="09:30" clearable />
			</div>
		</div>
	),
	play: async ({ canvasElement }) => {
		canvasElement.querySelector<HTMLInputElement>('[data-slot="time-picker"] input')?.click();
	},
};

// The time half of a date and time, opened at load: the same sheet, seconds
// off, beside the date trigger.
export const DateTimeOpen: StoryObj = {
	render: () => (
		<div className="p-8">
			<div className="w-80">
				<DateTimePicker aria-label="Starts" defaultValue={new Date(2026, 10, 12, 18, 45)} />
			</div>
		</div>
	),
	play: async ({ canvasElement }) => {
		canvasElement.querySelector<HTMLInputElement>('[data-slot="time-picker"] input')?.click();
	},
};

const meta: Meta = {
	title: "UI/TimePicker",
};

export default meta;
