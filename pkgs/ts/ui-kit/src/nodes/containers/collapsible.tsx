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
// Header pad-y 12 and content pad-top 8 per the kit density rules. The body
// is a stack (`layout.tsx`: `gap` 3, `padding`, `justify`, `align`,
// `divided`, the per child maps); the size props sit on the region. Open,
// the content is a flex column that may shrink, so a region capped by
// `max_height` / `height` scrolls its body under the trigger. It has no
// intrinsic width, so it fills.

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
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useSend,
	useSetProps,
	useStringProp,
} from "../../tree";
import { childHandlers, type LayoutDefaults, Stack, useLayout } from "./layout";

const DEFAULTS: LayoutDefaults = { gap: 3, justify: "start", align: "stretch" };

function CollapsibleView({ path }: NodeProps) {
	const open = useBoolProp(path, "open");
	const title = useStringProp(path, "title");
	const setProps = useSetProps(path);
	const send = useSend(path);
	const layout = useLayout(path, DEFAULTS);

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
			style={layout.size}
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
			<CollapsibleContent className="data-[state=open]:flex data-[state=open]:min-h-0 data-[state=open]:flex-col">
				<Stack path={path} layout={{ ...layout, size: undefined }} className="pt-2" />
			</CollapsibleContent>
		</CollapsiblePrimitive>
	);
}

export const Collapsible: NodeEntry = {
	component: CollapsibleView,
	fill: true,
	handlers: childHandlers,
};
