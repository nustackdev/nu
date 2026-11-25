// Popover -- a button that opens a small floating panel, children as its body.
//
// For settings and details that should take no room until asked for: the
// panel floats beside its trigger, so nothing in the flow moves when it
// opens. Escape, a click outside or the trigger close it.
//
// The trigger wears a Button's look off the same props a ButtonRef sends
// (`label`, `icon`, `tooltip`, `variant`, `size`), so an empty label draws a
// square icon button named by its tooltip. `title` heads the panel, a
// quiet line over the body. `side` puts the panel on that side of it and
// `edge` (start, center, end) lines their edges up.
//
// Two segments are the popover's own places, not body:
//   header   heads the panel in place of `title`, in a box that takes the
//            width and lets its child shrink; the panel is named by it
//   trigger  drawn inside the trigger button in place of `label` and
//            `icon`, in the same Button look (variant, size, tooltip), so
//            an avatar and a name are one button. Display only: a control
//            in there would be a button inside a button. The button is
//            named by `tooltip`, else `title`, else "Open"
// Python names them `popover.header` and `popover.trigger`.
//
// The tab owns `open` while the user clicks, the way Collapsible does: a
// toggle updates the local prop first, then emits `change` with the new
// `value` (open or not), which a read answers too. The server opens or closes it, and changes the trigger,
// through plain `write` payloads the default merge handles.
//
// Composes the kit Popover primitive (Radix under the hood), which owns the
// portal, motion, Esc and focus restore. Layout (`layout.tsx`): the panel is
// `width` wide (288px unless set), the size props sit on it, and the body
// is a stack (`gap` 3, `padding`, `justify`, `align`, `divided`, the per
// child maps). A body taller than the room left on screen scrolls.

import { useCallback, useId } from "react";
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
	EVENTS,
	FlowProvider,
	type NodeEntry,
	type NodeProps,
	SlotView,
	useBoolProp,
	useChildren,
	useEmit,
	useEnumProp,
	useSetProps,
	useStringProp,
} from "../../tree";
import { useDisabledScope } from "../input/control";
import { childHandlers, type LayoutDefaults, Stack, useLayout } from "./layout";
import { overlayStyle, readOpen } from "./modal";

const SIDES = ["top", "right", "bottom", "left"] as const;
const EDGES = ["start", "center", "end"] as const;
const DEFAULTS: LayoutDefaults = { gap: 3, justify: "start", align: "stretch" };
const HEADER = "header";
const TRIGGER = "trigger";
const SLOTS: ReadonlySet<string> = new Set([HEADER, TRIGGER]);

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
	const segments = useChildren(path);
	const hasHeader = segments.includes(HEADER);
	const hasTrigger = segments.includes(TRIGGER);
	const headerId = useId();
	const setProps = useSetProps(path);
	const emit = useEmit(path);

	const onOpenChange = useCallback(
		(next: boolean) => {
			setProps({ open: next });
			emit(EVENTS.change, { value: next });
		},
		[setProps, emit],
	);

	const Icon = iconFor(iconName);
	const iconOnly = Boolean(Icon) && label === "";
	const name = title || tooltip || label || iconName || "Open";
	const trigger = hasTrigger ? (
		<Button
			className="shrink-0"
			variant={variant}
			size={size}
			disabled={disabled}
			aria-label={tooltip || title || "Open"}
			type="button"
		>
			<SlotView path={path} segment={TRIGGER} flow="row" />
		</Button>
	) : iconOnly ? (
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
				aria-label={hasHeader ? undefined : name}
				aria-labelledby={hasHeader ? headerId : undefined}
				className={cn(
					"flex max-h-(--radix-popover-content-available-height) flex-col",
					!layout.scroll && "overflow-y-auto",
				)}
				style={overlayStyle(layout, [])}
			>
				{hasHeader ? (
					<div id={headerId} data-slot="popover-header" className="mb-3 min-w-0">
						<SlotView path={path} segment={HEADER} />
					</div>
				) : title ? (
					<div data-slot="popover-title" className="mb-3 text-sm font-medium text-text-primary">
						{title}
					</div>
				) : null}
				<FlowProvider flow="block">
					{/* The panel carries `padding` (overlayStyle), so the body adds none. */}
					<Stack
						path={path}
						layout={{ ...layout, size: undefined, padSet: false, padding: undefined }}
						skip={SLOTS}
					/>
				</FlowProvider>
			</PopoverContent>
		</PopoverPrimitive>
	);
}

export const Popover: NodeEntry = {
	component: PopoverView,
	handlers: childHandlers,
	reads: { "": readOpen },
};
