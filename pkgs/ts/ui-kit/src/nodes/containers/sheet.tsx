// Sheet -- edge drawer over the page, children as its body. Modal's sibling
// for inspectors and side panels.
//
// Server-owned `open` / `title`, plus `side`, `size` and `dismissible`, all
// plain props merged by the default `write`, so there is no handler here.
// When the user dismisses (backdrop, Escape, the close button) and
// `dismissible` is true, the sheet closes in this tab and sends `notify`
// with {open: false}, the same as Modal.
//
// Composes the kit Sheet primitive (Radix Dialog under the hood): portal,
// scrim, focus trap, Esc and focus restore come from it, and so do the slide
// (`slow`, no fade), pad 20 and radius `xl`. We own the header, the body and
// the notify. The body scrolls on its own under the header and stacks its
// children under a block flow.

import { OPS } from "@nustackdev/ui-core";
import { useCallback } from "react";
import {
	SheetContent,
	SheetHeader,
	Sheet as SheetPrimitive,
	SheetTitle,
} from "../../components/ui/sheet";
import { cn } from "../../lib/utils";
import {
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useEnumProp,
	useSend,
	useSetProps,
	useStringProp,
} from "../../tree";

const SIDES = ["left", "right", "top", "bottom"] as const;
const SIZES = ["sm", "md", "lg"] as const;

function SheetView({ path }: NodeProps) {
	const open = useBoolProp(path, "open");
	const title = useStringProp(path, "title");
	const side = useEnumProp(path, "side", SIDES, "right");
	const size = useEnumProp(path, "size", SIZES, "md");
	const dismissible = useBoolProp(path, "dismissible", true);
	const send = useSend(path);
	const setProps = useSetProps(path);

	// A dismiss closes in this tab and tells the program, like a Collapsible
	// toggle. A later write of `open: true` opens it again.
	const onOpenChange = useCallback(
		(next: boolean) => {
			if (next) return;
			if (!dismissible) return;
			setProps({ open: false });
			send(OPS.notify, { open: false });
		},
		[dismissible, send, setProps],
	);

	return (
		<SheetPrimitive open={open} onOpenChange={onOpenChange}>
			<SheetContent
				data-node="sheet"
				side={side}
				size={size}
				showClose={dismissible}
				aria-describedby={undefined}
			>
				{/* Radix needs a title to name the dialog; an untitled sheet keeps one for screen readers. */}
				<SheetHeader className={cn(!title && "sr-only", dismissible && "pr-8")}>
					<SheetTitle>{title || "Sheet"}</SheetTitle>
				</SheetHeader>
				<div className="-mx-5 -my-1 flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-5 py-1">
					<FlowProvider flow="block">
						<NodeChildren path={path} />
					</FlowProvider>
				</div>
			</SheetContent>
		</SheetPrimitive>
	);
}

export const Sheet: NodeEntry = { component: SheetView };
