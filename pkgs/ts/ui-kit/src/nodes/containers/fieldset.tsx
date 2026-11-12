// Fieldset -- grouped fields with a legend and shared vertical spacing.
// Legend, gap and disabled are plain props, merged by the default `write`,
// so there is no handler here. Children are the node's own children in the
// tree, rendered by `NodeChildren`.
//
// The `disabled` flag is visual-only -- we deliberately do not set the HTML
// `disabled` attribute on `<fieldset>` because that would cascade to child
// inputs. Uses semantic tokens (border-default, text-muted) instead of raw
// opacity for the disabled treatment.
//
// `min-w-0` on the fieldset: a browser gives `<fieldset>` a min inline size
// of its content, so without it a wide child (a table, a long line) widens
// the fieldset past the column that holds it.

import {
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useStringProp,
} from "../../tree";

const GAP_CLASSES: Record<string, string> = {
	sm: "gap-2",
	md: "gap-4",
	lg: "gap-6",
};

function FieldsetView({ path }: NodeProps) {
	const legend = useStringProp(path, "legend");
	const gap = useStringProp(path, "gap", "md");
	const disabled = useBoolProp(path, "disabled");

	const gapCls = GAP_CLASSES[gap] ?? GAP_CLASSES.md;
	const borderCls = disabled ? "border-border-subtle" : "border-border-default";
	const textCls = disabled ? "text-text-muted" : "text-text-primary";

	return (
		<fieldset
			className={`min-w-0 rounded-md border p-4 ${borderCls} ${textCls}`}
			aria-disabled={disabled || undefined}
		>
			{legend ? (
				<legend className="px-1 text-sm font-semibold text-text-secondary">{legend}</legend>
			) : null}
			<div className={`flex min-w-0 flex-col ${gapCls}`}>
				<FlowProvider flow="block">
					<NodeChildren path={path} indexed />
				</FlowProvider>
			</div>
		</fieldset>
	);
}

export const Fieldset: NodeEntry = { component: FieldsetView, fill: true };
