// Field -- labelled form-field wrapper around exactly one control. Label,
// help, error and required are plain props, merged by the default `write`
// and coerced at read time, so there is no handler here. `check` is the
// message a Form's own checks left (./../input/control.ts `validateUnder`);
// it shows when there is no `error`, and clears when the control is edited.
//
// Built on the kit Field (components/ui/field.tsx, a11y.md §5): a real
// `<label for>` pointing at the control, help that stays when an error shows,
// an error with `role="alert"`. The ids, the invalid and required state and
// the label ride `FieldContext` down to the control node, which puts them on
// the real element (`aria-describedby`, `aria-invalid`, `required`) and
// skips a label of its own. So an error turns the control red, and the Field
// label is the control's accessible name.
//
// The control is the first (and only expected) child in the tree. Extra
// children do not draw; a notice names them (the server refuses a second
// control where it is built). In a Form's values a Field stands for its
// control (`wraps`), never its `actions`.
//
// `actions` is a named child drawn at the end of the label row (the kit
// Field's `action`), in a row flow: an icon button, or a Popover of the
// field's settings. It sits outside the field's wiring, so an input in it is
// not the control, takes no label from it, and is not the field's value.
//
// `inline` draws it as one row: label in a left column `label_width` px
// wide (80 unless set), control, then actions; help and error under the
// control. Stacked inline fields line up into two columns.
// Layout (`layout.tsx`): the size props, `scroll`, and
// `gap` (1) between label, control and help.

import { Field as FieldChrome } from "../../components/ui/field";
import { Text } from "../../components/ui/text";
import { cn } from "../../lib/utils";
import {
	ACTIONS_SLOT,
	FlowProvider,
	type NodeEntry,
	type NodeProps,
	NodeView,
	SlotView,
	useBoolProp,
	useChildren,
	useNumberProp,
	useStringProp,
} from "../../tree";
import { useDisabledScope } from "../input/control";
import { gapClass, type LayoutDefaults, useLayout } from "./layout";
import { Unpaired } from "./unpaired";

const DEFAULTS: LayoutDefaults = { gap: 1 };

function FieldView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const help = useStringProp(path, "help");
	// The program's error wins over a failed check the form ran.
	const given = useStringProp(path, "error");
	const check = useStringProp(path, "check");
	const error = given || check;
	const required = useBoolProp(path, "required");
	const inline = useBoolProp(path, "inline");
	const labelWidth = useNumberProp(path, "label_width", 80);
	const scoped = useDisabledScope();
	const disabled = useBoolProp(path, "disabled") || scoped;
	const all = useChildren(path);
	const hasActions = all.includes(ACTIONS_SLOT);
	const children = all.filter((s) => s !== ACTIONS_SLOT);
	const layout = useLayout(path, DEFAULTS);
	const child = children[0];

	return (
		<FieldChrome
			label={label}
			help={help}
			error={error}
			required={required}
			disabled={disabled}
			inline={inline}
			labelWidth={labelWidth}
			action={hasActions ? <SlotView path={path} segment={ACTIONS_SLOT} flow="row" /> : undefined}
			className={cn(!inline && "flex flex-col", !inline && gapClass(layout), layout.scroll)}
			style={layout.size}
		>
			{child ? (
				<FlowProvider flow="block">
					<NodeView path={[...path, child]} />
				</FlowProvider>
			) : (
				<Text size="xs" tone="danger" mono>
					no child under {path.join(" / ")}
				</Text>
			)}
			<Unpaired path={path} segments={children.slice(1)} why="a Field holds one control" />
		</FieldChrome>
	);
}

export const Field: NodeEntry = { component: FieldView, fill: true, wraps: true };
