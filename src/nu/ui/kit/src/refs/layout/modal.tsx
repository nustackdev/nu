// Modal -- dialog overlay Section. Server-owned `open` / `title`; tab sends
// `notify` with {open: false} when the user dismisses (backdrop / Escape)
// and `dismissible` is true. Composes the kit Dialog primitive (Radix
// Dialog under the hood). Overlay + content pick up motion + backdrop tint
// from the primitive; we own the notify wiring only.
//
// TODO(retune): the legacy Modal kept children mounted while closed so
// child slice state survived across open/close cycles. Radix Dialog
// remounts by default. The current cut accepts that remount to avoid
// fighting Radix's mount lifecycle; slice state may reset when the modal
// closes. If persistence is required, wrap the body in `forceMount` and
// gate visibility with `hidden` at the wrapper level.

import { useCallback } from "react";
import { ErrorBoundary } from "../../components/ErrorBoundary";
import { OP_NOTIFY } from "@nustackdev/ui-core";
import {
	Dialog,
	DialogContent,
	DialogHeader,
	DialogTitle,
} from "../../components/ui/dialog";
import { renderers } from "../../refs";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const factory: SliceFactory = (path, ctx, props, children) => ({
	type: "Modal",
	value: null,
	open: typeof props?.open === "boolean" ? (props.open as boolean) : false,
	title: typeof props?.title === "string" ? (props.title as string) : "",
	dismissible: typeof props?.dismissible === "boolean" ? (props.dismissible as boolean) : true,
	children: Array.isArray(children) ? [...children] : [],
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as { open?: unknown; title?: unknown };
			if ("open" in p) {
				slice.open = p.open == null ? false : Boolean(p.open);
			}
			if ("title" in p) {
				slice.title = p.title == null ? "" : String(p.title);
			}
		}),
});

function ModalView({ path }: { path: string }) {
	const open = useStore((s) => Boolean(s.refs[path]?.open));
	const title = useStore((s) => (s.refs[path]?.title as string) ?? "");
	const dismissible = useStore((s) => Boolean(s.refs[path]?.dismissible));
	const childPaths = useStore((s) => (s.refs[path]?.children as string[]) ?? []);
	const refs = useStore((s) => s.refs);
	const send = useStore((s) => s.send);

	const onOpenChange = useCallback(
		(next: boolean) => {
			if (!next) {
				if (!dismissible) return;
				send({ op: OP_NOTIFY, ref: path, payload: { open: false } });
			}
		},
		[dismissible, path, send],
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
					{childPaths.map((cp) => {
						const childSlice = refs[cp];
						if (!childSlice) {
							return (
								<div key={cp} className="text-xs text-status-danger font-mono">
									no ref at {cp}
								</div>
							);
						}
						const Comp = renderers[childSlice.type];
						if (!Comp) {
							return (
								<div key={cp} className="text-xs text-status-danger font-mono">
									no renderer for {childSlice.type}
								</div>
							);
						}
						return (
							<ErrorBoundary key={cp} label={`${cp} (${childSlice.type})`}>
								<Comp path={cp} />
							</ErrorBoundary>
						);
					})}
				</div>
			</DialogContent>
		</Dialog>
	);
}

export const Modal: RefEntry = { factory, component: ModalView };
