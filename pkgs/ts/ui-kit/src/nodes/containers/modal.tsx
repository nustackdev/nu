// Modal -- dialog overlay Section. Server-owned `open` / `title`; when the
// user dismisses (backdrop, Escape, the close button) and `dismissible` is
// true, it closes in this tab and emits `change` with `value: false`. A
// read answers whether it is open (`readOpen`), the value a `change` carries.
//
// `open`, `title` and `dismissible` are plain props: the default `write`
// merges them and the coercions below handle nil at read time, so there is
// no handler here. There is no trigger slot: the opener is some other node
// that writes `open`.
//
// The child at segment "header" draws in the title's place, for a heading
// that is more than a string (an icon, a name, a badge). The modal only
// places it: a box that takes the width and lets its child shrink, kept
// clear of the close button, and the dialog's labelled title, so the dialog
// is named by its text. Python names it `modal.header`. Every other child
// renders in the dialog body. With neither, a hidden "Dialog" title still
// names it.
//
// Composes the kit Dialog primitive (Radix Dialog under the hood). Overlay +
// content pick up motion + backdrop tint from the primitive; we own the
// emit wiring only.
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

import { type CSSProperties, useCallback } from "react";
import {
	Dialog,
	DialogContent,
	DialogHeader,
	DialogTitle,
	DialogTitleBox,
} from "../../components/ui/dialog";
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
const HEADER = "header";
const SLOTS: ReadonlySet<string> = new Set([HEADER]);

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
	const hasHeader = useChildren(path).includes(HEADER);
	const emit = useEmit(path);
	const setProps = useSetProps(path);

	// A dismiss closes in this tab and tells the program, like a Collapsible
	// toggle. A later write of `open: true` opens it again.
	const onOpenChange = useCallback(
		(next: boolean) => {
			if (next) return;
			if (!dismissible) return;
			setProps({ open: false });
			emit(EVENTS.change, { value: false });
		},
		[dismissible, emit, setProps],
	);

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent
				showClose={dismissible}
				aria-describedby={undefined}
				className="flex max-h-[calc(100dvh-2rem)] flex-col"
				width={layout.size?.width}
				style={overlayStyle(layout, ["width"])}
			>
				{/* Radix needs a title to name the dialog; an untitled one keeps one for screen readers. */}
				<DialogHeader className={cn(!title && !hasHeader && "sr-only", dismissible && "pr-8")}>
					{hasHeader ? (
						<DialogTitleBox>
							<SlotView path={path} segment={HEADER} />
						</DialogTitleBox>
					) : (
						<DialogTitle>{title || "Dialog"}</DialogTitle>
					)}
				</DialogHeader>
				<div
					data-slot="modal-body"
					className={cn(
						"-m-1 flex min-h-0 min-w-0 flex-1 flex-col p-1",
						flowClass(layout, "column", { padding: false }),
						!layout.scroll && "overflow-y-auto",
					)}
					style={flowStyle({ ...layout, size: undefined })}
				>
					<StackChildren path={path} layout={layout} skip={SLOTS} />
				</div>
			</DialogContent>
		</Dialog>
	);
}

/** The main read of an overlay or a fold: whether it is open now. */
export const readOpen = (props: Record<string, unknown>): boolean => Boolean(props.open ?? false);

export const Modal: NodeEntry = {
	component: ModalView,
	handlers: childHandlers,
	reads: { "": readOpen },
};
