// AlertRef -- variant-tagged banner with title and body.
//
// Server-owned by default; `dismissible` flips on a notify-on-X path. The
// `write` op is a partial merge: missing keys leave the slice value untouched.
// Class-level defaults arrive on mount field `props` and seed the slice.

import { OP_NOTIFY } from "../../protocol";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const VARIANT_CLASSES: Record<string, string> = {
	info: "bg-blue-50 text-blue-900 border-blue-200",
	warn: "bg-yellow-50 text-yellow-900 border-yellow-200",
	ok: "bg-green-50 text-green-900 border-green-200",
	danger: "bg-red-50 text-red-900 border-red-200",
};

const factory: SliceFactory = (path, ctx, props) => ({
	type: "AlertRef",
	value: null,
	variant: typeof props?.variant === "string" ? (props.variant as string) : "info",
	title: typeof props?.title === "string" ? (props.title as string) : "",
	body: typeof props?.body === "string" ? (props.body as string) : "",
	dismissible: typeof props?.dismissible === "boolean" ? (props.dismissible as boolean) : false,
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as {
				variant?: unknown;
				title?: unknown;
				body?: unknown;
				dismissible?: unknown;
			};
			if ("variant" in p) {
				slice.variant = p.variant == null ? "info" : String(p.variant);
			}
			if ("title" in p) {
				slice.title = p.title == null ? "" : String(p.title);
			}
			if ("body" in p) {
				slice.body = p.body == null ? "" : String(p.body);
			}
			if ("dismissible" in p) {
				slice.dismissible = Boolean(p.dismissible);
			}
		}),
});

function AlertView({ path }: { path: string }) {
	const variant = useStore((s) => (s.refs[path]?.variant as string) ?? "info");
	const title = useStore((s) => (s.refs[path]?.title as string) ?? "");
	const body = useStore((s) => (s.refs[path]?.body as string) ?? "");
	const dismissible = useStore((s) => Boolean(s.refs[path]?.dismissible));
	const send = useStore((s) => s.send);
	const cls = VARIANT_CLASSES[variant] ?? VARIANT_CLASSES.info;
	return (
		<div role="alert" className={`flex items-start gap-3 rounded border px-3 py-2 text-sm ${cls}`}>
			<div className="flex-1">
				{title !== "" && <div className="font-semibold">{title}</div>}
				{body !== "" && <p className="mt-0.5 whitespace-pre-wrap">{body}</p>}
			</div>
			{dismissible && (
				<button
					type="button"
					aria-label="dismiss"
					className="ml-2 rounded px-1 text-current opacity-70 hover:opacity-100"
					onClick={() => send({ op: OP_NOTIFY, ref: path, payload: null })}
				>
					×
				</button>
			)}
		</div>
	);
}

export const AlertRef: RefEntry = { factory, component: AlertView };
