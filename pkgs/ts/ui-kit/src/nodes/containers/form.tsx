// Form -- a semantic <form> that stacks its children. The onSubmit handler
// exists solely to block the browser's native reload on Enter; submit logic
// lives on a child Button.
//
// Children are its own, in the tree. Chrome (`title`) is a
// plain prop, merged by the default `write`. Layout (`layout.tsx`): a
// stack's layers, `padding` (0), `gap` (4), `justify`, `align` (stretch),
// `divided`, the size props and the per child maps.

import { Heading } from "../../components/ui/heading";
import { cn } from "../../lib/utils";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";
import {
	childHandlers,
	flowClass,
	flowStyle,
	type LayoutDefaults,
	StackChildren,
	useLayout,
} from "./layout";

const DEFAULTS: LayoutDefaults = { gap: 4, padding: 0, justify: "start", align: "stretch" };

function FormView({ path }: NodeProps) {
	const title = useStringProp(path, "title");
	const layout = useLayout(path, DEFAULTS);
	return (
		<form
			onSubmit={(e) => e.preventDefault()}
			className={cn("flex flex-col", flowClass(layout, "column"))}
			style={flowStyle(layout)}
		>
			{title ? (
				<Heading as="h3" size="xl" className="mb-2">
					{title}
				</Heading>
			) : null}
			<StackChildren path={path} layout={layout} />
		</form>
	);
}

export const Form: NodeEntry = { component: FormView, fill: true, handlers: childHandlers };
