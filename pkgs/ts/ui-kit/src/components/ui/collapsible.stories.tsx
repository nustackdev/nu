import type { Meta, StoryObj } from "@storybook/react-vite";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import { Badge } from "./badge";
import { Button } from "./button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "./collapsible";
import { rowTriggerProps, TriggerRow, TriggerRowHeader } from "./trigger-row";

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

// A header row that holds controls: the trigger keeps only the chevron and
// takes its name from the header box; a click on the text or the empty space
// toggles, the button does its own thing.
function SampleHeader() {
	const [stops, setStops] = useState(0);
	return (
		<Collapsible>
			<TriggerRow className="rounded-md px-2 py-3">
				<CollapsibleTrigger
					{...rowTriggerProps}
					aria-labelledby="sample-header"
					className="group flex shrink-0 items-center rounded-sm outline-hidden"
				>
					<ChevronRight
						aria-hidden
						className="size-4 text-text-secondary transition-transform duration-fast ease-out group-data-[state=open]:rotate-90"
					/>
				</CollapsibleTrigger>
				<TriggerRowHeader id="sample-header">
					<div className="flex min-w-0 items-center gap-2">
						<span className="min-w-0 flex-1 truncate text-sm font-medium text-text-primary">
							run_tests tests/nustd/ui with a long name that truncates
						</span>
						<Badge variant="warn">running</Badge>
						<Button size="sm" variant="ghost" onClick={() => setStops((n) => n + 1)}>
							Stop{stops ? ` (${stops})` : ""}
						</Button>
					</div>
				</TriggerRowHeader>
			</TriggerRow>
			<CollapsibleContent>
				<div className="mt-2 rounded-md border border-border-subtle bg-bg-sunken p-3 text-sm text-text-primary">
					Output folds away under the header row.
				</div>
			</CollapsibleContent>
		</Collapsible>
	);
}

export const Header: StoryObj = {
	render: () => (
		<div className="p-8 max-w-md">
			<SampleHeader />
		</div>
	),
};

export const Matrix = Default;

const meta: Meta = {
	title: "UI/Collapsible",
};

export default meta;
