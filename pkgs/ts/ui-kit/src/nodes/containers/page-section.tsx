// PageSection -- a titled part of a page: a heading, a line under it,
// actions on the right, and a body of children. On the wire it is
// `PageSection` (Python's PageSectionRef).
//
// Composes the kit Section primitive (a semantic <section>). Chrome is plain
// props, merged by the default store `write`: `title`, `description`, `size`
// ("md" or "lg", the space between header and body), `bordered` (a hairline
// over the section, for one section after another) and `gap` (a spacing
// step between the body's children). Unknown values fall back.
//
// The child at segment "actions" is the header's action area: drawn on the
// right of the title, in a row flow, so a Button or a Row of them sits there
// at its own size. Python names it `section.actions`. Every other child is
// the body, in insertion order, stacked in a block flow the way a Column
// stacks them. No header is drawn with no title, description or actions.

import { Section as SectionPrimitive } from "../../components/ui/section";
import { GAP_CLASSES, stepClass } from "../../lib/steps";
import { cn } from "../../lib/utils";
import {
	ACTIONS_SLOT,
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	SlotView,
	useBoolProp,
	useChildren,
	useEnumProp,
	useNumberProp,
	useStringProp,
} from "../../tree";

const SIZES = ["md", "lg"] as const;
const SLOTS: ReadonlySet<string> = new Set([ACTIONS_SLOT]);

function PageSectionView({ path }: NodeProps) {
	const title = useStringProp(path, "title");
	const description = useStringProp(path, "description");
	const size = useEnumProp(path, "size", SIZES, "md");
	const bordered = useBoolProp(path, "bordered");
	const gap = useNumberProp(path, "gap", 4);
	const segments = useChildren(path);
	const hasActions = segments.includes(ACTIONS_SLOT);
	const hasBody = segments.some((s) => !SLOTS.has(s));

	return (
		<SectionPrimitive
			size={size}
			bordered={bordered}
			title={title || undefined}
			description={description || undefined}
			actions={hasActions ? <SlotView path={path} segment={ACTIONS_SLOT} flow="row" /> : undefined}
		>
			{hasBody ? (
				<div
					data-slot="section-body"
					className={cn("flex min-w-0 flex-col", stepClass(GAP_CLASSES, gap))}
				>
					<FlowProvider flow="block">
						<NodeChildren path={path} skip={SLOTS} />
					</FlowProvider>
				</div>
			) : null}
		</SectionPrimitive>
	);
}

export const PageSection: NodeEntry = { component: PageSectionView, fill: true };
