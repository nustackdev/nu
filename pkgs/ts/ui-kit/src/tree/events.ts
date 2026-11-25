// events.ts -- the shared event names a node emits.

/**
 * The shared event names, the browser's half of `nustd.ui.core.events`.
 * A domain event (`edit`, `sort`, `move`, ...) is a plain string at its node.
 */
export const EVENTS = {
	input: "input",
	change: "change",
	submit: "submit",
	click: "click",
	action: "action",
	dismiss: "dismiss",
	select: "select",
} as const;
