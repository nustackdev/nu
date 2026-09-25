import type { Meta, StoryObj } from "@storybook/react-vite";
import { OverflowTooltip } from "./overflow-tooltip";
import { TooltipProvider } from "./tooltip";

const SHORT = "Roadmap";
const LONG = "Quarterly roadmap for the storage engine rewrite and its migration";

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
			<TooltipProvider>
				<div className="w-48 space-y-2 text-sm text-text-primary">
					{[SHORT, LONG].map((title) => (
						<OverflowTooltip key={title} label={title} side="right">
							<button type="button" className="block w-full truncate text-left">
								{title}
							</button>
						</OverflowTooltip>
					))}
				</div>
			</TooltipProvider>
		</div>
	),
};

const meta: Meta = {
	title: "UI/OverflowTooltip",
};

export default meta;
