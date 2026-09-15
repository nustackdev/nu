// Field -- labelled form-field wrapper. Display-only chrome around exactly
// one child node. Label, help, error and required are plain props, merged by
// the default `write` and coerced at read time the way the old factory
// coerced them at write time, so there is no handler here.
//
// The single child used to arrive as a one-entry `children` path list. Now
// it is the node's first (and only expected) child in the tree: we take the
// first segment from `useChildren` and render it ourselves rather than via
// `NodeChildren`, because the control has to sit inside the
// aria-describedby / aria-invalid wrapper. Any extra children are ignored,
// same as the old module ignored a `children` list that was not length 1.
// Wires aria-invalid / aria-describedby per a11y.md §5.

import { useId } from "react";
import { Text } from "../../components/ui/text";
import {
	type NodeEntry,
	type NodeProps,
	NodeView,
	useBoolProp,
	useChildren,
	useStringProp,
} from "../../tree";

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
						<span className="text-accent ml-0.5" aria-hidden>
							*
						</span>
					) : null}
				</Text>
			) : null}
			<div aria-describedby={describedBy} aria-invalid={hasError || undefined}>
				{child ? (
					<NodeView path={[...path, child]} />
				) : (
					<Text size="xs" tone="danger" mono>
						no child under {path.join(" / ")}
					</Text>
				)}
			</div>
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

export const Field: NodeEntry = { component: FieldView };
