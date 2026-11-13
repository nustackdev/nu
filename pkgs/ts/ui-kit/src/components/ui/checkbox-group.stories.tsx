import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { CheckboxGroup } from "./checkbox-group";

const SIZES = ["sm", "md", "lg"] as const;
const GENRES = ["drama", "comedy", "sci-fi", "documentary"].map((value) => ({
	value,
	label: value,
}));

function Sample() {
	const [value, setValue] = useState(["drama", "sci-fi"]);
	return (
		<CheckboxGroup aria-label="Genres" options={GENRES} value={value} onValueChange={setValue} />
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
		<div className="p-8 space-y-6">
			<div>
				<Label>sizes</Label>
				<div className="flex items-start gap-8">
					{SIZES.map((s) => (
						<CheckboxGroup
							key={s}
							aria-label={s}
							size={s}
							options={GENRES.slice(0, 2)}
							value={["drama"]}
							onValueChange={noop}
						/>
					))}
				</div>
			</div>
			<div>
				<Label>horizontal</Label>
				<CheckboxGroup
					aria-label="horizontal"
					orientation="horizontal"
					options={GENRES}
					value={["comedy"]}
					onValueChange={noop}
				/>
			</div>
			<div>
				<Label>states</Label>
				<div className="flex items-start gap-8">
					<CheckboxGroup
						aria-label="disabled"
						disabled
						options={GENRES.slice(0, 2)}
						value={["drama"]}
						onValueChange={noop}
					/>
					<CheckboxGroup
						aria-label="readonly"
						readOnly
						options={GENRES.slice(0, 2)}
						value={["comedy"]}
						onValueChange={noop}
					/>
					<CheckboxGroup
						aria-label="invalid"
						invalid
						options={GENRES.slice(0, 2)}
						value={[]}
						onValueChange={noop}
					/>
				</div>
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/CheckboxGroup",
};

export default meta;
