// AlertRef -- variant-tagged banner with title and body.
//
// Server-owned by default; `dismissible` flips on a notify-on-X path. Every
// mutation is a partial merge of chrome keys into the node's props, which is
// exactly what the store's default write does, so there is no handler here.
// Nil on the wire reads back as the class default at render time. Composes
// the kit Alert primitive: variant maps to tone; the primitive owns the
// icon/bg/border trio, we own the dismiss notify wiring.

import { OPS } from "@nustackdev/ui-core";
import { X } from "lucide-react";
import { Alert, AlertDescription, AlertIcon, AlertTitle } from "../../components/ui/alert";
import { IconButton } from "../../components/ui/icon-button";
import { type NodeEntry, type NodeProps, useBoolProp, useSend, useStringProp } from "../../tree";

type Tone = "info" | "warn" | "ok" | "danger" | "neutral";

const VARIANT_TO_TONE: Record<string, Tone> = {
	info: "info",
	warn: "warn",
	ok: "ok",
	danger: "danger",
};

function AlertView({ path }: NodeProps) {
	const variant = useStringProp(path, "variant", "info");
	const title = useStringProp(path, "title");
	const body = useStringProp(path, "body");
	const dismissible = useBoolProp(path, "dismissible");
	const send = useSend(path);
	const tone = VARIANT_TO_TONE[variant] ?? "neutral";
	return (
		<Alert tone={tone}>
			<AlertIcon />
			<div className="flex-1">
				{title !== "" && <AlertTitle>{title}</AlertTitle>}
				{body !== "" && <AlertDescription className="whitespace-pre-wrap">{body}</AlertDescription>}
			</div>
			{dismissible && (
				<IconButton variant="ghost" size="sm" aria-label="dismiss" onClick={() => send(OPS.notify)}>
					<X />
				</IconButton>
			)}
		</Alert>
	);
}

export const AlertRef: NodeEntry = { component: AlertView };
