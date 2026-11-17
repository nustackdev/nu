// Popover -- a button that opens a small floating panel, children as its body.
//
// For settings and details that should take no room until asked for: the
// panel floats beside its trigger, so nothing in the flow moves when it
// opens. Escape, a click outside or the trigger close it.
//
// The trigger wears a Button's look off the same props a ButtonRef sends
// (`label`, `icon`, `tooltip`, `variant`, `size`), so an empty label draws a
// square icon button named by its tooltip. `title` heads the panel, a
// quiet line over the body. `side` puts the panel on that
// side of it and `edge` (start, center, end) lines their edges up.
//
// The tab owns `open` while the user clicks, the way Collapsible does: a
// toggle updates the local prop first, then ships a `notify` with
// {open: bool}. The server opens or closes it, and changes the trigger,
// through plain `write` payloads the default merge handles.
//
// Composes the kit Popover primitive (Radix under the hood), which owns the
// portal, motion, Esc and focus restore. Layout (`layout.tsx`): the panel is
// `width` wide (288px unless set), the size props sit on it, and the body
// is a stack (`gap` 3, `padding`, `justify`, `align`, `divided`, the per
// child maps). A body taller than the room left on screen scrolls.

import { OPS } from "@nustackdev/ui-core";
import { useCallback } from "react";
import { Button } from "../../components/ui/button";
import { IconButton } from "../../components/ui/icon-button";
import {
	PopoverContent,
	Popover as PopoverPrimitive,
	PopoverTrigger,
} from "../../components/ui/popover";
import {
	Tooltip,
	TooltipContent,
	TooltipProvider,
	TooltipTrigger,
} from "../../components/ui/tooltip";
import { BUTTON_SIZES, kitVariant } from "../../lib/button-look";
import { iconFor } from "../../lib/icons";
import { cn } from "../../lib/utils";
import {
	FlowProvider,
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useEnumProp,
	useSend,
	useSetProps,
	useStringProp,
} from "../../tree";
import { useDisabledScope } from "../input/control";
import { childHandlers, type LayoutDefaults, Stack, useLayout } from "./layout";
import { overlayStyle } from "./modal";

const SIDES = ["top", "right", "bottom", "left"] as const;
const EDGES = ["start", "center", "end"] as const;
const DEFAULTS: LayoutDefaults = { gap: 3, justify: "start", align: "stretch" };

function PopoverView({ path }: NodeProps) {
	const open = useBoolProp(path, "open");
	const label = useStringProp(path, "label");
	const title = useStringProp(path, "title");
	const iconName = useStringProp(path, "icon");
	const tooltip = useStringProp(path, "tooltip");
	const variant = kitVariant(useStringProp(path, "variant", "ghost"));
	const size = useEnumProp(path, "size", BUTTON_SIZES, "sm");
	const side = useEnumProp(path, "side", SIDES, "bottom");
	const edge = useEnumProp(path, "edge", EDGES, "end");
	const scoped = useDisabledScope();
	const disabled = useBoolProp(path, "disabled") || scoped;
	const layout = useLayout(path, DEFAULTS);
	const setProps = useSetProps(path);
	const send = useSend(path);

	const onOpenChange = useCallback(
		(next: boolean) => {
			setProps({ open: next });
			send(OPS.notify, { open: next });
		},
		[setProps, send],
	);

	const Icon = iconFor(iconName);
	const iconOnly = Boolean(Icon) && label === "";
	const name = title || tooltip || label || iconName || "Open";
	const trigger = iconOnly ? (
		<IconButton
			className="shrink-0"
			variant={variant}
			size={size}
			disabled={disabled}
			aria-label={name}
			type="button"
		>
			{Icon && <Icon aria-hidden />}
		</IconButton>
	) : (
		<Button className="shrink-0" variant={variant} size={size} disabled={disabled} type="button">
			{Icon && <Icon aria-hidden />}
			{label === "" ? name : label}
		</Button>
	);

	const opener = <PopoverTrigger asChild>{trigger}</PopoverTrigger>;

	return (
		<PopoverPrimitive open={open && !disabled} onOpenChange={onOpenChange}>
			{tooltip ? (
				<TooltipProvider>
					<Tooltip>
						<TooltipTrigger asChild>{opener}</TooltipTrigger>
						<TooltipContent>{tooltip}</TooltipContent>
					</Tooltip>
				</TooltipProvider>
			) : (
				opener
			)}
			<PopoverContent
				data-node="popover"
				side={side}
				align={edge}
				aria-label={name}
				className={cn(
					"flex max-h-(--radix-popover-content-available-height) flex-col",
					!layout.scroll && "overflow-y-auto",
				)}
				style={overlayStyle(layout, [])}
			>
				{title ? (
					<div data-slot="popover-title" className="mb-3 text-sm font-medium text-text-primary">
						{title}
					</div>
				) : null}
				<FlowProvider flow="block">
					{/* The panel carries `padding` (overlayStyle), so the body adds none. */}
					<Stack
						path={path}
						layout={{ ...layout, size: undefined, padSet: false, padding: undefined }}
					/>
				</FlowProvider>
			</PopoverContent>
		</PopoverPrimitive>
	);
}

export const Popover: NodeEntry = { component: PopoverView, handlers: childHandlers };
