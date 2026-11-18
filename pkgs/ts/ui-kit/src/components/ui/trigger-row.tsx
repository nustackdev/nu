// TriggerRow -- a disclosure's trigger row whose header may hold controls.
// Design refs:
//   a11y.md          §3 Collapsible / Accordion (one trigger keeps Space/Enter)
//   cursor.md        (clickable rows wear the arrow)
//   motion.md        (hover wash on `duration-fast`, ease-out)
//
// A Radix trigger is a <button>, and a header with a button, a switch or a
// link in it cannot sit inside one. So the row splits in two: the trigger
// keeps only the chevron (and Space/Enter, aria-expanded, aria-controls,
// its name read off the header box by aria-labelledby), and the header box
// sits beside it. The row wears the hover, press and focus ring the trigger
// used to, and a click on its text or empty space clicks the trigger. A
// click on a control in the header, or on the trigger itself, is left
// alone, so the control does its own thing and nothing toggles twice.
//
// The trigger is marked `data-row-trigger`; the row finds its own one (not
// one in a nested row). Callers place the trigger and the header box, so
// the chevron sits at the start (Collapsible) or the end (Accordion).

import type * as React from "react";
import { cn } from "../../lib/utils";

/** What handles its own click inside a header row: the row leaves these alone. */
const CONTROLS = [
	"a[href]",
	"button",
	"input",
	"select",
	"textarea",
	"label",
	"summary",
	"[contenteditable]:not([contenteditable='false'])",
	"[role=button]",
	"[role=link]",
	"[role=switch]",
	"[role=checkbox]",
	"[role=radio]",
	"[role=slider]",
	"[role=combobox]",
	"[role=menuitem]",
	"[role=tab]",
	"[role=option]",
].join(", ");

/** Props that mark the row's own trigger. Spread on the Radix trigger. */
export const rowTriggerProps = { "data-row-trigger": "" } as const;

function clickTrigger(e: React.MouseEvent<HTMLDivElement>) {
	const row = e.currentTarget;
	const hit = (e.target as Element).closest(CONTROLS);
	if (hit && row.contains(hit)) return;
	// A drag that selected header text is a selection, not a toggle.
	if (!(window.getSelection()?.isCollapsed ?? true)) return;
	const triggers = row.querySelectorAll<HTMLElement>("[data-row-trigger]");
	for (const t of triggers) {
		if (t.closest("[data-slot=trigger-row]") === row) return t.click();
	}
}

export function TriggerRow({ className, onClick, ...props }: React.ComponentProps<"div">) {
	return (
		// The trigger inside carries the keyboard; this click is the mouse's
		// wider target for it, so the row needs no key handler or role.
		// biome-ignore lint/a11y/noStaticElementInteractions: see above.
		// biome-ignore lint/a11y/useKeyWithClickEvents: see above.
		<div
			data-slot="trigger-row"
			onClick={(e) => {
				onClick?.(e);
				if (!e.defaultPrevented) clickTrigger(e);
			}}
			className={cn(
				"group/row flex w-full min-w-0 items-center gap-2 cursor-default",
				"transition-colors duration-fast ease-out",
				"hover:bg-bg-hover active:bg-bg-press",
				"has-[[data-row-trigger]:focus-visible]:ring-2 has-[[data-row-trigger]:focus-visible]:ring-ring",
				"has-[[data-row-trigger]:focus-visible]:ring-offset-2 has-[[data-row-trigger]:focus-visible]:ring-offset-bg-canvas",
				className,
			)}
			{...props}
		/>
	);
}

/**
 * The header box: takes the row's free width and lets its child shrink, so a
 * one-line text inside truncates. Its id names the trigger.
 */
export function TriggerRowHeader({ className, ...props }: React.ComponentProps<"div">) {
	return (
		<div
			data-slot="trigger-row-header"
			className={cn("flex min-w-0 flex-1 flex-col justify-center", className)}
			{...props}
		/>
	);
}
