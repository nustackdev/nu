import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { Autocomplete } from "./autocomplete";

const SIZES = ["sm", "md", "lg"] as const;
const CITIES = ["Amsterdam", "Athens", "Berlin", "Lisbon", "London", "Madrid", "Yerevan"].map(
	(value) => ({ value, label: value }),
);

function Sample({
	seed = "",
	...rest
}: {
	seed?: string;
	disabled?: boolean;
	readOnly?: boolean;
	invalid?: boolean;
	size?: "sm" | "md" | "lg";
}) {
	const [value, setValue] = useState(seed);
	return (
		<Autocomplete
			aria-label="City"
			placeholder="Type a city"
			options={CITIES}
			value={value}
			onValueChange={setValue}
			onPick={setValue}
			{...rest}
		/>
	);
}

const Label = ({ children }: { children: string }) => (
	<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">{children}</div>
);

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-sm">
			<Sample />
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6 max-w-sm">
			<div>
				<Label>sizes</Label>
				<div className="space-y-3">
					{SIZES.map((s) => (
						<Sample key={s} size={s} seed="Lisbon" />
					))}
				</div>
			</div>
			<div>
				<Label>states</Label>
				<div className="space-y-3">
					<Sample seed="Free text is fine" />
					<Sample seed="Disabled" disabled />
					<Sample seed="Readonly" readOnly />
					<Sample seed="Atlantis" invalid />
				</div>
			</div>
		</div>
	),
};

// Opened at load (an arrow down on the field): in touch mode a bottom sheet
// with the field on top and the suggestions as rows, on desktop the list
// under the field.
export const Open: StoryObj = {
	render: () => (
		<div className="p-8 max-w-sm">
			<Sample seed="l" />
		</div>
	),
	play: async ({ canvasElement }) => {
		const field = canvasElement.querySelector<HTMLInputElement>('[data-slot="autocomplete"] input');
		field?.focus();
		field?.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }));
	},
};

const meta: Meta = {
	title: "UI/Autocomplete",
};

export default meta;
