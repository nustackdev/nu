// Sheet -- edge drawer over the page, children as its body. Modal's sibling
// for inspectors and side panels.
//
// Server-owned `open` / `title`, plus `side` and `dismissible`, all plain
// props merged by the default `write`. The child at segment "header" draws
// in the title's place, for a heading that is more than a string; the sheet
// only places it, in a box that takes the width and lets its child shrink,
// kept clear of the close button. That box is the sheet's labelled title,
// so the sheet is named by its text. Python names it `sheet.header`; every
// other child is the body. Layout (`layout.tsx`): a left or right
// sheet is `width` wide (440px unless set), a top or bottom one `height` tall
// (320px unless set); `padding` replaces its pad, and the body speaks a
// stack's layers (`gap` 4, `justify`, `align`, `divided`, the per child
// maps).
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
	SheetTitleBox,
} from "../../components/ui/sheet";
import { cn } from "../../lib/utils";
import {
	type NodeEntry,
	type NodeProps,
	SlotView,
	useBoolProp,
	useChildren,
	useEnumProp,
	useSend,
	useSetProps,
	useStringProp,
} from "../../tree";
import {
	childHandlers,
	flowClass,
	flowStyle,
	type LayoutDefaults,
	StackChildren,
	useLayout,
} from "./layout";
import { overlayStyle } from "./modal";

const SIDES = ["left", "right", "top", "bottom"] as const;
const DEFAULTS: LayoutDefaults = { gap: 4, justify: "start", align: "stretch" };
const HEADER = "header";
const SLOTS: ReadonlySet<string> = new Set([HEADER]);

function SheetView({ path }: NodeProps) {
	const open = useBoolProp(path, "open");
	const title = useStringProp(path, "title");
	const side = useEnumProp(path, "side", SIDES, "right");
	const layout = useLayout(path, DEFAULTS);
	const dismissible = useBoolProp(path, "dismissible", true);
	const hasHeader = useChildren(path).includes(HEADER);
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
				showClose={dismissible}
				aria-describedby={undefined}
				width={layout.size?.width}
				height={layout.size?.height}
				style={overlayStyle(layout, ["width", "height"])}
			>
				{/* Radix needs a title to name the dialog; an untitled sheet keeps one for screen readers. */}
				<SheetHeader className={cn(!title && !hasHeader && "sr-only", dismissible && "pr-8")}>
					{hasHeader ? (
						<SheetTitleBox>
							<SlotView path={path} segment={HEADER} />
						</SheetTitleBox>
					) : (
						<SheetTitle>{title || "Sheet"}</SheetTitle>
					)}
				</SheetHeader>
				<div
					className={cn(
						"-mx-5 -my-1 flex min-h-0 flex-1 flex-col px-5 py-1",
						flowClass(layout, "column", { padding: false }),
						!layout.scroll && "overflow-y-auto",
					)}
					style={flowStyle({ ...layout, size: undefined })}
				>
					<StackChildren path={path} layout={layout} skip={SLOTS} />
				</div>
			</SheetContent>
		</SheetPrimitive>
	);
}

export const Sheet: NodeEntry = { component: SheetView, handlers: childHandlers };
