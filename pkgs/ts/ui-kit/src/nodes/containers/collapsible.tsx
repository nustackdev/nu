// Collapsible -- one titled region whose children fold away.
//
// A trigger row (chevron + title) over a body of open-ended children. The tab
// owns `open` while the user clicks, the way Accordion does: a toggle updates
// the local prop first, then emits `change` with the new `value` (open or
// not), which a read answers too. The server
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
//
// A `header` child, when there is one, is the trigger row's content in place
// of `title`, and the body skips it. It may hold controls, so it cannot sit
// in the trigger <button>: the row is a `TriggerRow` (components/ui), the
// trigger keeps only the chevron and takes its name from the header box,
// and a click on the row's text or empty space clicks the trigger. A control
// in the header does its own thing and does not toggle.

import { ChevronRight } from "lucide-react";
import { useCallback, useId } from "react";
import {
	CollapsibleContent,
	Collapsible as CollapsiblePrimitive,
	CollapsibleTrigger,
} from "../../components/ui/collapsible";
import { rowTriggerProps, TriggerRow, TriggerRowHeader } from "../../components/ui/trigger-row";
import { cn } from "../../lib/utils";
import {
	EVENTS,
	type NodeEntry,
	type NodeProps,
	SlotView,
	useBoolProp,
	useChildren,
	useEmit,
	useSetProps,
	useStringProp,
} from "../../tree";
import { childHandlers, type LayoutDefaults, Stack, useLayout } from "./layout";
import { readOpen } from "./modal";

const DEFAULTS: LayoutDefaults = { gap: 3, justify: "start", align: "stretch" };
const HEADER = "header";
const SLOTS: ReadonlySet<string> = new Set([HEADER]);

const ROW = "rounded-md px-2 py-3";
const TITLE = "text-base font-medium text-text-primary";
const FOCUS =
	"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas";

function Chevron() {
	return (
		<ChevronRight
			aria-hidden
			className={cn(
				"pointer-events-none size-4 shrink-0 text-text-secondary",
				"transition-transform duration-fast ease-out",
				"group-data-[state=open]:rotate-90",
			)}
		/>
	);
}

function CollapsibleView({ path }: NodeProps) {
	const open = useBoolProp(path, "open");
	const title = useStringProp(path, "title");
	const setProps = useSetProps(path);
	const emit = useEmit(path);
	const layout = useLayout(path, DEFAULTS);
	const hasHeader = useChildren(path).includes(HEADER);
	const headerId = useId();

	const onOpenChange = useCallback(
		(next: boolean) => {
			setProps({ open: next });
			emit(EVENTS.change, { value: next });
		},
		[setProps, emit],
	);

	return (
		<CollapsiblePrimitive
			data-node="collapsible"
			open={open}
			onOpenChange={onOpenChange}
			className="flex flex-col"
			style={layout.size}
		>
			{hasHeader ? (
				<TriggerRow className={ROW}>
					<CollapsibleTrigger
						{...rowTriggerProps}
						aria-labelledby={headerId}
						className="group flex shrink-0 items-center rounded-sm outline-hidden"
					>
						<Chevron />
					</CollapsibleTrigger>
					<TriggerRowHeader id={headerId}>
						<SlotView path={path} segment={HEADER} />
					</TriggerRowHeader>
				</TriggerRow>
			) : (
				<CollapsibleTrigger
					aria-label={title ? undefined : "Toggle section"}
					className={cn(
						"group flex w-full items-center gap-2 text-left",
						ROW,
						TITLE,
						"transition-colors duration-fast ease-out",
						"hover:bg-bg-hover active:bg-bg-press",
						FOCUS,
					)}
				>
					<Chevron />
					<span className="min-w-0 truncate">{title}</span>
				</CollapsibleTrigger>
			)}
			<CollapsibleContent className="data-[state=open]:flex data-[state=open]:min-h-0 data-[state=open]:flex-col">
				<Stack path={path} layout={{ ...layout, size: undefined }} className="pt-2" skip={SLOTS} />
			</CollapsibleContent>
		</CollapsiblePrimitive>
	);
}

export const Collapsible: NodeEntry = {
	component: CollapsibleView,
	fill: true,
	handlers: childHandlers,
	reads: { "": readOpen },
};
