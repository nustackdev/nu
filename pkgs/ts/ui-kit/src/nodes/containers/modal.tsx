// Modal -- dialog overlay Section. Server-owned `open` / `title`; when the
// user dismisses (backdrop, Escape, the close button) and `dismissible` is
// true, it closes in this tab and sends `notify` with {open: false}.
//
// `open`, `title` and `dismissible` are plain props: the default `write`
// merges them and the coercions below handle nil at read time, so there is
// no handler here. There is no trigger slot: the opener is some other node
// that writes `open`, so every child renders in the dialog body.
//
// Composes the kit Dialog primitive (Radix Dialog under the hood). Overlay +
// content pick up motion + backdrop tint from the primitive; we own the
// notify wiring only.
//
// Layout (`layout.tsx`): `width` is the dialog's width (512px unless set),
// the other size props sit on the dialog too, `padding` replaces its pad, and
// the body speaks a stack's layers (`gap` 4, `justify`, `align`, `divided`,
// the per child maps). The dialog never grows past the window: it caps at
// the viewport height less a margin, the title stays put and the body
// scrolls (`scroll` says another way). The body pads itself a little and
// takes it back with a negative margin, so a focus ring on a child at the
// edge is not clipped by the scroll.
//
// Radix Dialog unmounts the body while closed. Node props live in the tree
// so they survive a close, but component-local state may reset. If more is
// required, wrap the body in `forceMount` and gate visibility with `hidden`
// at the wrapper level.

import { OPS } from "@nustackdev/ui-core";
import { type CSSProperties, useCallback } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../../components/ui/dialog";
import { cn } from "../../lib/utils";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useSend,
	useSetProps,
	useStringProp,
} from "../../tree";
import {
	childHandlers,
	flowClass,
	flowStyle,
	type Layout,
	type LayoutDefaults,
	StackChildren,
	stepLength,
	useLayout,
} from "./layout";

const DEFAULTS: LayoutDefaults = { gap: 4, justify: "start", align: "stretch" };

/**
 * An overlay's size and pad as a style, less the props the primitive takes
 * by name (`width`, and a sheet's `height`).
 */
export function overlayStyle(
	layout: Layout,
	named: readonly ("width" | "height")[],
): CSSProperties {
	const style: CSSProperties = { ...layout.size };
	for (const name of named) delete style[name];
	if (layout.padSet) style.padding = stepLength(layout.padding ?? 0);
	return style;
}

function ModalView({ path }: NodeProps) {
	const open = useBoolProp(path, "open");
	const layout = useLayout(path, DEFAULTS);
	const title = useStringProp(path, "title");
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
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent
				showClose={dismissible}
				className="flex max-h-[calc(100dvh-2rem)] flex-col"
				width={layout.size?.width}
				style={overlayStyle(layout, ["width"])}
			>
				{title ? (
					<DialogHeader>
						<DialogTitle>{title}</DialogTitle>
					</DialogHeader>
				) : null}
				<div
					data-slot="modal-body"
					className={cn(
						"-m-1 flex min-h-0 min-w-0 flex-1 flex-col p-1",
						flowClass(layout, "column", { padding: false }),
						!layout.scroll && "overflow-y-auto",
					)}
					style={flowStyle({ ...layout, size: undefined })}
				>
					<StackChildren path={path} layout={layout} />
				</div>
			</DialogContent>
		</Dialog>
	);
}

export const Modal: NodeEntry = { component: ModalView, handlers: childHandlers };
