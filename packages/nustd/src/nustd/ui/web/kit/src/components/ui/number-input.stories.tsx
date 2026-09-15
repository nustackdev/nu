import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { NumberInput } from "./number-input";

const SIZES = ["sm", "md", "lg"] as const;

function Controlled({
	size,
	variant,
	invalid,
	disabled,
	initial = 42,
}: {
	size?: "sm" | "md" | "lg";
	variant?: "default" | "ghost" | "filled";
	invalid?: boolean;
	disabled?: boolean;
	initial?: number | null;
}) {
	const [v, setV] = useState<number | null>(initial);
	return (
		<div className="w-32">
			<NumberInput
				size={size}
				variant={variant}
				invalid={invalid}
				disabled={disabled}
				value={v}
				onValueChange={setV}
				min={0}
				max={100}
			/>
		</div>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<Controlled />
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
					<div className="flex items-end gap-3">
						{SIZES.map((s) => (
							<div key={s}>
								<div className="mb-1 font-mono text-xs text-text-muted">{s}</div>
								<Controlled size={s} />
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						states
					</div>
					<div className="flex flex-wrap items-end gap-3">
						<Controlled />
						<Controlled disabled />
						<Controlled invalid />
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/NumberInput",
};

export default meta;
