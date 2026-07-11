import type { Meta, StoryObj } from "@storybook/react-vite";
import { Button } from "./button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./tooltip";

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<TooltipProvider>
					<Tooltip>
						<TooltipTrigger asChild>
							<Button variant="secondary">Hover me</Button>
						</TooltipTrigger>
						<TooltipContent>Tooltip content</TooltipContent>
					</Tooltip>
				</TooltipProvider>
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8">
				<TooltipProvider>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						sides
					</div>
					<div className="grid grid-cols-2 gap-6">
						<Tooltip>
							<TooltipTrigger asChild>
								<Button variant="secondary">Top</Button>
							</TooltipTrigger>
							<TooltipContent side="top">Top hint</TooltipContent>
						</Tooltip>
						<Tooltip>
							<TooltipTrigger asChild>
								<Button variant="secondary">Right</Button>
							</TooltipTrigger>
							<TooltipContent side="right">Right hint</TooltipContent>
						</Tooltip>
						<Tooltip>
							<TooltipTrigger asChild>
								<Button variant="secondary">Bottom</Button>
							</TooltipTrigger>
							<TooltipContent side="bottom">Bottom hint</TooltipContent>
						</Tooltip>
						<Tooltip>
							<TooltipTrigger asChild>
								<Button variant="secondary">Left</Button>
							</TooltipTrigger>
							<TooltipContent side="left">Left hint</TooltipContent>
						</Tooltip>
					</div>
				</TooltipProvider>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Tooltip",
};

export default meta;
