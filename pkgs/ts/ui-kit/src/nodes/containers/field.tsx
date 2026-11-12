// Field -- labelled form-field wrapper. Display-only chrome around exactly
// one child node. Label, help, error and required are plain props, merged by
// the default `write` and coerced at read time the way the old factory
// coerced them at write time, so there is no handler here.
//
// The single child used to arrive as a one-entry `children` path list. Now
// it is the node's first (and only expected) child in the tree: we take the
// first segment from `useChildren` and render it ourselves rather than via
// `NodeChildren`, because the control has to sit inside the
// aria-describedby / aria-invalid wrapper. Extra children do not draw; a
// notice names them (the server refuses a second control where it is built).
// Wires aria-invalid / aria-describedby per a11y.md §5.

import { useId } from "react";
import { Text } from "../../components/ui/text";
import {
	FlowProvider,
	type NodeEntry,
	type NodeProps,
	NodeView,
	useBoolProp,
	useChildren,
	useStringProp,
} from "../../tree";
import { Unpaired } from "./unpaired";

function FieldView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const help = useStringProp(path, "help");
	const error = useStringProp(path, "error");
	const required = useBoolProp(path, "required");
	const children = useChildren(path);
	const helpId = useId();
	const errorId = useId();

	const hasError = error.length > 0;
	const child = children[0];
	const showBottom = hasError || help.length > 0;
	const describedBy = hasError ? errorId : help ? helpId : undefined;

	return (
		<div className="flex flex-col gap-1">
			{label ? (
				<Text as="span" size="sm" tone={hasError ? "danger" : "secondary"} weight="medium">
					{label}
					{required ? (
						<span className="text-accent-text ml-0.5" aria-hidden>
							*
						</span>
					) : null}
				</Text>
			) : null}
			<div aria-describedby={describedBy} aria-invalid={hasError || undefined}>
				{child ? (
					<FlowProvider flow="block">
						<NodeView path={[...path, child]} />
					</FlowProvider>
				) : (
					<Text size="xs" tone="danger" mono>
						no child under {path.join(" / ")}
					</Text>
				)}
			</div>
			<Unpaired path={path} segments={children.slice(1)} why="a Field holds one control" />
			{showBottom ? (
				<Text
					id={hasError ? errorId : helpId}
					as="span"
					size="xs"
					tone={hasError ? "danger" : "secondary"}
				>
					{hasError ? error : help}
				</Text>
			) : null}
		</div>
	);
}

export const Field: NodeEntry = { component: FieldView, fill: true };
