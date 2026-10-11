// Collapsible -- one titled region whose children fold away.
//
// A trigger row (chevron + title) over a body of open-ended children. The tab
// owns `open` while the user clicks, the way Accordion does: a toggle updates
// the local prop first, then ships a `notify` with {open: bool}. The server
// can still open or close it, and change the title, through plain `write`
// payloads ({open}, {title}) that the default merge handles, so there is no
// handler here.
//
// Composes the kit Collapsible primitive (Radix under the hood), which owns
// the content height motion (`base`, ease-in-out) and Space/Enter. The
// chevron points right when closed and turns down when open, like a tree row.
// Header pad-y 12 and content pad-top 8 per the kit density rules. Children
// stack under a block flow; the region has no intrinsic width, so it fills.

import { OPS } from "@nustackdev/ui-core";
import { ChevronRight } from "lucide-react";
import { useCallback } from "react";
import {
	CollapsibleContent,
	Collapsible as CollapsiblePrimitive,
	CollapsibleTrigger,
} from "../../components/ui/collapsible";
import { cn } from "../../lib/utils";
import {
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useSend,
	useSetProps,
	useStringProp,
} from "../../tree";

function CollapsibleView({ path }: NodeProps) {
	const open = useBoolProp(path, "open");
	const title = useStringProp(path, "title");
	const setProps = useSetProps(path);
	const send = useSend(path);

	const onOpenChange = useCallback(
		(next: boolean) => {
			setProps({ open: next });
			send(OPS.notify, { open: next });
		},
		[setProps, send],
	);

	return (
		<CollapsiblePrimitive
			data-node="collapsible"
			open={open}
			onOpenChange={onOpenChange}
			className="flex flex-col"
		>
			<CollapsibleTrigger
				aria-label={title ? undefined : "Toggle section"}
				className={cn(
					"group flex w-full items-center gap-2 rounded-md px-2 py-3 text-left",
					"text-base font-medium text-text-primary",
					"transition-colors duration-fast ease-out",
					"hover:bg-bg-hover active:bg-bg-press",
					"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
				)}
			>
				<ChevronRight
					aria-hidden
					className={cn(
						"pointer-events-none size-4 shrink-0 text-text-secondary",
						"transition-transform duration-fast ease-out",
						"group-data-[state=open]:rotate-90",
					)}
				/>
				<span className="min-w-0 truncate">{title}</span>
			</CollapsibleTrigger>
			<CollapsibleContent>
				<div className="flex flex-col gap-3 pt-2">
					<FlowProvider flow="block">
						<NodeChildren path={path} />
					</FlowProvider>
				</div>
			</CollapsibleContent>
		</CollapsiblePrimitive>
	);
}

export const Collapsible: NodeEntry = { component: CollapsibleView, fill: true };
