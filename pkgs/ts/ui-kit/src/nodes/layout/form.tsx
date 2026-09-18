// Form -- semantic <form> Section. Stacks its children vertically with gap,
// padding, and cross-axis alignment. The onSubmit handler exists solely to
// block the browser's native reload on Enter; submit logic lives on a child
// Button node.
//
// Children are the node's own children in the tree, rendered by
// `NodeChildren`. Chrome is plain props, merged by the default `write`, so
// there is no handler here.
//
// TODO(retune): same dynamic-class concern as Column: numeric gap /
// padding template raw Tailwind class names. We map the discrete step
// ladder statically here so the JIT sees every candidate at build time.
// A `Form` primitive with named tokens is the follow-up.

import { Heading } from "../../components/ui/heading";
import {
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useNumberProp,
	useStringProp,
} from "../../tree";

const GAP_CLASSES: Record<number, string> = {
	0: "gap-0",
	1: "gap-1",
	2: "gap-2",
	3: "gap-3",
	4: "gap-4",
	5: "gap-5",
	6: "gap-6",
	8: "gap-8",
	10: "gap-10",
	12: "gap-12",
};

const PADDING_CLASSES: Record<number, string> = {
	0: "p-0",
	1: "p-1",
	2: "p-2",
	3: "p-3",
	4: "p-4",
	5: "p-5",
	6: "p-6",
	8: "p-8",
	10: "p-10",
	12: "p-12",
};

const ALIGN_CLASSES: Record<string, string> = {
	start: "items-start",
	center: "items-center",
	end: "items-end",
	stretch: "items-stretch",
};

function FormView({ path }: NodeProps) {
	const title = useStringProp(path, "title");
	const gap = useNumberProp(path, "gap", 4);
	const padding = useNumberProp(path, "padding", 0);
	const align = useStringProp(path, "align", "stretch");

	const gapCls = GAP_CLASSES[gap] ?? GAP_CLASSES[4];
	const padCls = PADDING_CLASSES[padding] ?? PADDING_CLASSES[0];
	const alignCls = ALIGN_CLASSES[align] ?? ALIGN_CLASSES.stretch;

	return (
		<form
			onSubmit={(e) => e.preventDefault()}
			className={`flex flex-col ${gapCls} ${padCls} ${alignCls}`}
		>
			{title ? (
				<Heading as="h3" size="xl" className="mb-2">
					{title}
				</Heading>
			) : null}
			<NodeChildren path={path} />
		</form>
	);
}

export const Form: NodeEntry = { component: FormView };
