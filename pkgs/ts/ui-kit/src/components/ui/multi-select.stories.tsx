import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { MultiSelect } from "./multi-select";

const SIZES = ["sm", "md", "lg"] as const;
const PACKAGES = ["nu", "nustd", "nudle", "nulog", "nuspace", "virtuals", "invisibles"].map(
	(value) => ({ value, label: value }),
);

function Sample({ seed = ["nu", "nustd"] }: { seed?: string[] }) {
	const [value, setValue] = useState(seed);
	return (
		<MultiSelect
			aria-label="Packages"
			className="w-64"
			options={PACKAGES}
			value={value}
			onValueChange={setValue}
			placeholder="Pick packages"
		/>
	);
}

const Label = ({ children }: { children: string }) => (
	<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">{children}</div>
);

const noop = () => {};

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
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
						<MultiSelect
							key={s}
							aria-label={s}
							size={s}
							options={PACKAGES}
							value={["nu"]}
							onValueChange={noop}
						/>
					))}
				</div>
			</div>
			<div>
				<Label>states</Label>
				<div className="space-y-3">
					<Sample seed={[]} />
					<Sample seed={["nu", "nustd", "nudle", "nulog"]} />
					<MultiSelect
						aria-label="disabled"
						disabled
						options={PACKAGES}
						value={["nu"]}
						onValueChange={noop}
					/>
					<MultiSelect
						aria-label="invalid"
						invalid
						options={PACKAGES}
						value={[]}
						placeholder="Pick at least one"
						onValueChange={noop}
					/>
				</div>
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/MultiSelect",
};

export default meta;
