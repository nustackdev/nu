// Fieldset -- grouped fields with a legend. Legend and disabled are plain
// props, merged by the default `write`. Children are its own,
// in the tree, a stack (`layout.tsx`: `padding` 4 on the fieldset, `gap` 4,
// `justify`, `align`, `divided`, the size props, the per child maps).
//
// The `disabled` flag is visual-only -- we deliberately do not set the HTML
// `disabled` attribute on `<fieldset>` because that would cascade to child
// inputs. Uses semantic tokens (border-default, text-muted) instead of raw
// opacity for the disabled treatment.
//
// `min-w-0` on the fieldset: a browser gives `<fieldset>` a min inline size
// of its content, so without it a wide child (a table, a long line) widens
// the fieldset past the column that holds it. The fieldset is a flex column,
// so a body capped by `max_height` / `height` shrinks and scrolls under the
// legend instead of running past the border.

import { cn } from "../../lib/utils";
import { type NodeEntry, type NodeProps, useBoolProp, useStringProp } from "../../tree";
import { childHandlers, type LayoutDefaults, padClass, Stack, useLayout } from "./layout";

const DEFAULTS: LayoutDefaults = { gap: 4, padding: 4, justify: "start", align: "stretch" };

function FieldsetView({ path }: NodeProps) {
	const legend = useStringProp(path, "legend");
	const disabled = useBoolProp(path, "disabled");
	const layout = useLayout(path, DEFAULTS);

	const borderCls = disabled ? "border-border-subtle" : "border-border-default";
	const textCls = disabled ? "text-text-muted" : "text-text-primary";

	return (
		<fieldset
			className={cn(
				"flex min-w-0 flex-col rounded-md border",
				padClass(layout),
				borderCls,
				textCls,
			)}
			style={layout.size}
			aria-disabled={disabled || undefined}
		>
			{legend ? (
				<legend className="px-1 text-sm font-semibold text-text-secondary">{legend}</legend>
			) : null}
			<Stack path={path} layout={{ ...layout, padding: undefined, size: undefined }} />
		</fieldset>
	);
}

export const Fieldset: NodeEntry = { component: FieldsetView, fill: true, handlers: childHandlers };
