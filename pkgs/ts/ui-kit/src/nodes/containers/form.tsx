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
import { GAP_CLASSES, PADDING_CLASSES, stepClass } from "../../lib/steps";
import {
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useNumberProp,
	useStringProp,
} from "../../tree";

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

	const gapCls = stepClass(GAP_CLASSES, gap);
	const padCls = stepClass(PADDING_CLASSES, padding);
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
			<FlowProvider flow="block">
				<NodeChildren path={path} />
			</FlowProvider>
		</form>
	);
}

export const Form: NodeEntry = { component: FormView, fill: true };
