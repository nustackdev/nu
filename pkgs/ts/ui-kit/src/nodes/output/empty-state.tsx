// EmptyStateRef -- what a region says while it has nothing to show.
//
// Server-owned. A write is a partial merge of `label` / `description` /
// `size` / `icon` / `action` / `action_href` / `action_target` into the
// node's props, which is the default store behaviour, so there are no
// handlers. Composes the kit
// EmptyState primitive.
//
// `icon` is a lucide name (../../lib/icons), drawn
// above the label. `action` is the label of the way out, a small secondary
// button under the text: a click sends a notify (`on_action` on the server).
// With `action_href` it is a link that looks like that button instead, a
// real <a> under the Button primitive (`asChild`, as a ButtonRef with an
// href), opened per `action_target`, and the click still notifies.

import { OPS } from "@nustackdev/ui-core";
import { Button } from "../../components/ui/button";
import { EmptyState } from "../../components/ui/empty-state";
import { anchorProps } from "../../lib/anchor";
import { iconFor } from "../../lib/icons";
import { type NodeEntry, type NodeProps, useEnumProp, useSend, useStringProp } from "../../tree";

const SIZES = ["sm", "md"] as const;

function EmptyStateView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const description = useStringProp(path, "description");
	const size = useEnumProp(path, "size", SIZES, "md");
	const Icon = iconFor(useStringProp(path, "icon"));
	const action = useStringProp(path, "action");
	const actionHref = useStringProp(path, "action_href");
	const actionTarget = useStringProp(path, "action_target", "_self");
	const send = useSend(path);
	const onAction = () => send(OPS.notify);
	const button =
		action === "" ? undefined : actionHref !== "" ? (
			// The primitive's Slot hands its onClick to the <a>, as on a ButtonRef link.
			<Button variant="secondary" size="sm" asChild onClick={onAction}>
				<a {...anchorProps(actionHref, actionTarget)}>{action}</a>
			</Button>
		) : (
			<Button variant="secondary" size="sm" onClick={onAction}>
				{action}
			</Button>
		);
	return (
		<EmptyState
			size={size}
			icon={Icon ? <Icon aria-hidden /> : undefined}
			description={description || undefined}
			action={button}
		>
			{label}
		</EmptyState>
	);
}

export const EmptyStateRef: NodeEntry = { component: EmptyStateView, fill: true };
