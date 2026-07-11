import type { Meta, StoryObj } from "@storybook/react-vite";
import { ChevronDown } from "lucide-react";
import { Button } from "./button";
import {
	Collapsible,
	CollapsibleContent,
	CollapsibleTrigger,
} from "./collapsible";

function Sample() {
	return (
		<Collapsible>
			<CollapsibleTrigger asChild>
				<Button variant="ghost">
					Show details
					<ChevronDown />
				</Button>
			</CollapsibleTrigger>
			<CollapsibleContent>
				<div className="mt-2 rounded-md border border-border-subtle bg-bg-sunken p-3 text-sm text-text-primary">
					Hidden content revealed by the trigger. Height animates via
					--radix-collapsible-content-height.
				</div>
			</CollapsibleContent>
		</Collapsible>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-md">
				<Sample />
			</div>
	),
};

export const Matrix = Default;

const meta: Meta = {
	title: "UI/Collapsible",
};

export default meta;
