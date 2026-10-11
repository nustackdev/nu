// ButtonRef -- click trigger. Sends a notify on each click. No value.
//
// Chrome (label, variant, disabled, icon, tooltip) is props, seeded at the
// slot and merged by any later write, which is the default store behaviour,
// so there is no handler here. Composes the kit Button primitive; variant
// maps to a Button variant.
//
// `icon` is a lucide name resolved through the curated map in ./icons. With
// a label it draws before the text. With an empty label the node is an
// IconButton, named by `tooltip` (or the icon name) for screen readers. An
// unknown icon draws the label alone, and with no label either the path is
// shown, so a button that just appeared stays locatable. `tooltip`, when set,
// is the kit Tooltip on hover and focus. nudle mounts no TooltipProvider, so
// the node brings its own. A button keeps its size in a Row (`shrink-0`): a
// squeezed control is never what a crowded line wants.

import { OPS } from "@nustackdev/ui-core";
import type * as React from "react";
import { Button } from "../../components/ui/button";
import { IconButton } from "../../components/ui/icon-button";
import {
	Tooltip,
	TooltipContent,
	TooltipProvider,
	TooltipTrigger,
} from "../../components/ui/tooltip";
import { type NodeEntry, type NodeProps, useBoolProp, useSend, useStringProp } from "../../tree";
import { iconFor } from "./icons";

type ButtonVariant = "default" | "secondary" | "ghost" | "soft" | "destructive";

const VARIANT_TO_KIT: Record<string, ButtonVariant> = {
	primary: "default",
	secondary: "secondary",
	ghost: "ghost",
	soft: "soft",
	danger: "destructive",
};

function ButtonView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const variant = useStringProp(path, "variant", "primary");
	const disabled = useBoolProp(path, "disabled");
	const iconName = useStringProp(path, "icon");
	const tooltip = useStringProp(path, "tooltip");
	const send = useSend(path);
	const kitVariant = VARIANT_TO_KIT[variant] ?? "default";
	const Icon = iconFor(iconName);
	const onClick = () => {
		if (disabled) return;
		send(OPS.notify);
	};
	const button =
		Icon && label === "" ? (
			<IconButton
				className="shrink-0"
				variant={kitVariant}
				disabled={disabled}
				aria-label={tooltip || iconName}
				onClick={onClick}
			>
				<Icon aria-hidden />
			</IconButton>
		) : (
			<Button className="shrink-0" variant={kitVariant} disabled={disabled} onClick={onClick}>
				{Icon && <Icon aria-hidden />}
				{label === "" ? path.join(" / ") : label}
			</Button>
		);
	return tooltip ? <Hint text={tooltip}>{button}</Hint> : button;
}

function Hint({ text, children }: { text: string; children: React.ReactElement }) {
	return (
		<TooltipProvider>
			<Tooltip>
				<TooltipTrigger asChild>{children}</TooltipTrigger>
				<TooltipContent>{text}</TooltipContent>
			</Tooltip>
		</TooltipProvider>
	);
}

export const ButtonRef: NodeEntry = { component: ButtonView };
