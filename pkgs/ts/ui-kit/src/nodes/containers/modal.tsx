// Modal -- dialog overlay Section. Server-owned `open` / `title`; when the
// user dismisses (backdrop, Escape, the close button) and `dismissible` is
// true, it closes in this tab and sends `notify` with {open: false}.
//
// `open`, `title` and `dismissible` are plain props: the default `write`
// merges them and the read-time coercions below apply the same nil handling
// the old factory did, so there is no handler here. There is no trigger
// slot -- the legacy Modal never had one, the opener is some other node that
// writes `open` -- so every child renders in the dialog body via
// `NodeChildren`.
//
// Composes the kit Dialog primitive (Radix Dialog under the hood). Overlay +
// content pick up motion + backdrop tint from the primitive; we own the
// notify wiring only.
//
// TODO(retune): the legacy Modal kept children mounted while closed so child
// state survived across open/close cycles. Radix Dialog remounts by default.
// The current cut accepts that remount to avoid fighting Radix's mount
// lifecycle; node props live in the tree so they survive, but component-local
// state may reset when the modal closes. If more is required, wrap the body
// in `forceMount` and gate visibility with `hidden` at the wrapper level.

import { OPS } from "@nustackdev/ui-core";
import { useCallback } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../../components/ui/dialog";
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

function ModalView({ path }: NodeProps) {
	const open = useBoolProp(path, "open");
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
			<DialogContent showClose={dismissible}>
				{title ? (
					<DialogHeader>
						<DialogTitle>{title}</DialogTitle>
					</DialogHeader>
				) : null}
				<div className="flex flex-col gap-4">
					<FlowProvider flow="block">
						<NodeChildren path={path} />
					</FlowProvider>
				</div>
			</DialogContent>
		</Dialog>
	);
}

export const Modal: NodeEntry = { component: ModalView };
