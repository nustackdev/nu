// AlertRef -- variant-tagged banner with title and body.
//
// Server-owned by default; `dismissible` flips on a notify-on-X path. The
// `write` op is a partial merge: missing keys leave the slice value untouched.
// Class-level defaults arrive on mount field `props` and seed the slice.
// Composes the kit Alert primitive: variant maps to tone; the primitive owns
// the icon/bg/border trio, we own the dismiss notify wiring.

import { X } from "lucide-react";
import { OP_NOTIFY } from "@nustackdev/ui-core";
import {
	Alert,
	AlertDescription,
	AlertIcon,
	AlertTitle,
} from "../../components/ui/alert";
import { IconButton } from "../../components/ui/icon-button";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

type Tone = "info" | "warn" | "ok" | "danger" | "neutral";

const VARIANT_TO_TONE: Record<string, Tone> = {
	info: "info",
	warn: "warn",
	ok: "ok",
	danger: "danger",
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
	const tone = VARIANT_TO_TONE[variant] ?? "neutral";
	return (
		<Alert tone={tone}>
			<AlertIcon />
			<div className="flex-1">
				{title !== "" && <AlertTitle>{title}</AlertTitle>}
				{body !== "" && (
					<AlertDescription className="whitespace-pre-wrap">{body}</AlertDescription>
				)}
			</div>
			{dismissible && (
				<IconButton
					variant="ghost"
					size="sm"
					aria-label="dismiss"
					onClick={() => send({ op: OP_NOTIFY, ref: path, payload: null })}
				>
					<X />
				</IconButton>
			)}
		</Alert>
	);
}

export const AlertRef: RefEntry = { factory, component: AlertView };
