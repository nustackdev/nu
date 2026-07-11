// Modal -- dialog overlay Section. Server-owned `open` / `title`; tab sends
// `notify` with {open: false} when the user dismisses (backdrop / Escape)
// and `dismissible` is true. Children are kept mounted while closed so
// their slices keep state across open/close cycles.

import { useCallback, useEffect } from "react";
import { ErrorBoundary } from "../../components/ErrorBoundary";
import { OP_NOTIFY } from "@nustackdev/ui-core";
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

	const dismiss = useCallback(() => {
		if (!dismissible) return;
		send({ op: OP_NOTIFY, ref: path, payload: { open: false } });
	}, [dismissible, path, send]);

	useEffect(() => {
		if (!open) return;
		const onKey = (e: KeyboardEvent) => {
			if (e.key === "Escape") dismiss();
		};
		window.addEventListener("keydown", onKey);
		return () => window.removeEventListener("keydown", onKey);
	}, [open, dismiss]);

	const body = (
		<div className="flex flex-col gap-4">
			{childPaths.map((cp) => {
				const childSlice = refs[cp];
				if (!childSlice) {
					return (
						<div key={cp} className="text-xs text-destructive font-mono">
							no ref at {cp}
						</div>
					);
				}
				const Comp = renderers[childSlice.type];
				if (!Comp) {
					return (
						<div key={cp} className="text-xs text-destructive font-mono">
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
	);

	// Always-mounted wrapper preserves child slice state across open/close.
	return (
		<div hidden={!open} aria-hidden={!open}>
			<button
				type="button"
				className="fixed inset-0 z-40 cursor-default bg-black/50"
				onClick={dismiss}
				aria-label="close modal"
			/>
			<div
				role="dialog"
				aria-modal="true"
				className="fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-md border border-border bg-background p-6 shadow-lg"
			>
				{title ? <h3 className="mb-4 text-base font-semibold">{title}</h3> : null}
				{body}
			</div>
		</div>
	);
}

export const Modal: RefEntry = { factory, component: ModalView };
