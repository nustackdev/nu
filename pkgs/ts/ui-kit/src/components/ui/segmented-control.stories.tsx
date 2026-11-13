import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { SegmentedControl, SegmentedControlItem } from "./segmented-control";

const SIZES = ["sm", "md", "lg"] as const;
const RANGES = ["Day", "Week", "Month"];

function Sample() {
	const [value, setValue] = useState("Week");
	return (
		<SegmentedControl aria-label="Range" value={value} onValueChange={setValue}>
			{RANGES.map((r) => (
				<SegmentedControlItem key={r} value={r}>
					{r}
				</SegmentedControlItem>
			))}
		</SegmentedControl>
	);
}

const Label = ({ children }: { children: string }) => (
	<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">{children}</div>
);

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
			<Sample />
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6 max-w-xl">
			<div>
				<Label>sizes</Label>
				<div className="flex items-center gap-6">
					{SIZES.map((s) => (
						<SegmentedControl key={s} aria-label={s} size={s} defaultValue="Day">
							{RANGES.map((r) => (
								<SegmentedControlItem key={r} value={r}>
									{r}
								</SegmentedControlItem>
							))}
						</SegmentedControl>
					))}
				</div>
			</div>
			<div>
				<Label>states</Label>
				<div className="space-y-3">
					<SegmentedControl aria-label="none picked">
						{RANGES.map((r) => (
							<SegmentedControlItem key={r} value={r}>
								{r}
							</SegmentedControlItem>
						))}
					</SegmentedControl>
					<SegmentedControl aria-label="disabled" disabled defaultValue="Week">
						{RANGES.map((r) => (
							<SegmentedControlItem key={r} value={r}>
								{r}
							</SegmentedControlItem>
						))}
					</SegmentedControl>
					<SegmentedControl aria-label="invalid" invalid defaultValue="Month">
						{RANGES.map((r) => (
							<SegmentedControlItem key={r} value={r}>
								{r}
							</SegmentedControlItem>
						))}
					</SegmentedControl>
					<SegmentedControl aria-label="fill" fill defaultValue="Day">
						{RANGES.map((r) => (
							<SegmentedControlItem key={r} value={r}>
								{r}
							</SegmentedControlItem>
						))}
					</SegmentedControl>
				</div>
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/SegmentedControl",
};

export default meta;
