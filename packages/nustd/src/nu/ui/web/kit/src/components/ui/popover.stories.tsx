import type { Meta, StoryObj } from "@storybook/react-vite";
import { Button } from "./button";
import { Popover, PopoverContent, PopoverTrigger } from "./popover";

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<Popover>
					<PopoverTrigger asChild>
						<Button variant="secondary">Open popover</Button>
					</PopoverTrigger>
					<PopoverContent>
						<div className="space-y-1.5">
							<div className="text-sm font-medium text-text-primary">Popover</div>
							<div className="text-sm text-text-secondary">
								Anchored, not focus-trapping.
							</div>
						</div>
					</PopoverContent>
				</Popover>
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-16">
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					sides
				</div>
				<div className="grid grid-cols-2 gap-8">
					{(["top", "right", "bottom", "left"] as const).map((side) => (
						<Popover key={side}>
							<PopoverTrigger asChild>
								<Button variant="secondary">{side}</Button>
							</PopoverTrigger>
							<PopoverContent side={side}>
								<div className="text-sm text-text-primary">Anchored {side}.</div>
							</PopoverContent>
						</Popover>
					))}
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Popover",
};

export default meta;
