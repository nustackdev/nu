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
// control (`wraps`). Layout (`layout.tsx`): the size props, `scroll`, and
// `gap` (1) between label, control and help.

import { Field as FieldChrome } from "../../components/ui/field";
import { Text } from "../../components/ui/text";
import { cn } from "../../lib/utils";
import {
	FlowProvider,
	type NodeEntry,
	type NodeProps,
	NodeView,
	useBoolProp,
	useChildren,
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
	const scoped = useDisabledScope();
	const disabled = useBoolProp(path, "disabled") || scoped;
	const children = useChildren(path);
	const layout = useLayout(path, DEFAULTS);
	const child = children[0];

	return (
		<FieldChrome
			label={label}
			help={help}
			error={error}
			required={required}
			disabled={disabled}
			className={cn("flex flex-col", gapClass(layout), layout.scroll)}
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
