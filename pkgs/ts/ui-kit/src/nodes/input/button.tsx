// ButtonRef -- click trigger. Sends `{event: "click"}` on each click. No value.
//
// `submit` makes it a form's submit button (`type="submit"`; every other
// button is `type="button"`, so a Cancel in a Form never submits). Its name
// is its segment, so the Form's submit payload says which button fired.
// `loading` draws a spinner in place of the icon and takes no clicks.
//
// Chrome (label, variant, size, disabled, icon, tooltip, href, target) is
// props, seeded at the slot and merged by any later write, which is the
// default store behaviour, so there is no handler here. Composes the kit
// Button primitive; variant maps to a Button variant, size to its size.
//
// `href` makes it a link that looks like a button: the primitive renders
// `asChild` around a real <a>, so cmd-click opens a tab and a host's
// AnchorCatcher routes a same-origin one without a reload. This is the
// button-look link: LinkRef has no button looks. A click still sends
// the notify, so `on_click` hears it either way. A disabled link drops its
// href, since an anchor has no disabled state of its own.
//
// `icon` is a lucide name, resolved through ../../lib/icons. With
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
import { anchorProps } from "../../lib/anchor";
import { BUTTON_SIZES, kitVariant } from "../../lib/button-look";
import { iconFor } from "../../lib/icons";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useEnumProp,
	useSend,
	useStringProp,
} from "../../tree";
import { EVENTS, useDisabledScope, useForm } from "./control";

function ButtonView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const variant = kitVariant(useStringProp(path, "variant", "primary"));
	const size = useEnumProp(path, "size", BUTTON_SIZES, "md");
	// A disabled Fieldset or Form disables its buttons too.
	const scoped = useDisabledScope();
	const disabled = useBoolProp(path, "disabled") || scoped;
	const submit = useBoolProp(path, "submit");
	// A busy Form spins its submit buttons until the program clears it.
	const form = useForm();
	const loading = useBoolProp(path, "loading") || (submit && Boolean(form?.busy));
	const autoFocus = useBoolProp(path, "autofocus");
	const iconName = useStringProp(path, "icon");
	const tooltip = useStringProp(path, "tooltip");
	const href = useStringProp(path, "href");
	const target = useStringProp(path, "target", "_self");
	const send = useSend(path);
	const Icon = iconFor(iconName);
	const onClick = () => {
		if (disabled || loading) return;
		send(OPS.notify, { event: EVENTS.click });
	};
	const iconOnly = Boolean(Icon) && label === "";
	const content = iconOnly ? (
		Icon && <Icon aria-hidden />
	) : (
		<>
			{Icon && <Icon aria-hidden />}
			{label === "" ? path.join(" / ") : label}
		</>
	);
	// A link renders the same primitive around an <a>; a disabled one keeps
	// the look and loses the href. The primitive's Slot hands its onClick to
	// the <a>, so a link click notifies too.
	const link = href !== "";
	const linkChild = link ? (
		<a
			{...(disabled ? {} : anchorProps(href, target))}
			aria-disabled={disabled || undefined}
			className={disabled ? "pointer-events-none opacity-50" : undefined}
		>
			{content}
		</a>
	) : null;
	const button = iconOnly ? (
		<IconButton
			className="shrink-0"
			variant={variant}
			size={size}
			disabled={link ? undefined : disabled || loading}
			aria-busy={loading || undefined}
			aria-label={tooltip || iconName}
			asChild={link}
			type={submit ? "submit" : "button"}
			name={submit ? path[path.length - 1] : undefined}
			autoFocus={autoFocus}
			onClick={onClick}
		>
			{linkChild ?? content}
		</IconButton>
	) : (
		<Button
			className="shrink-0"
			variant={variant}
			size={size}
			disabled={link ? undefined : disabled}
			loading={link ? undefined : loading}
			asChild={link}
			type={submit ? "submit" : "button"}
			name={submit ? path[path.length - 1] : undefined}
			autoFocus={autoFocus}
			onClick={onClick}
		>
			{linkChild ?? content}
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
