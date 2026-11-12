// PageSection -- a titled part of a page: a heading, a line under it,
// actions on the right, and a body of children. On the wire it is
// `PageSection` (Python's PageSectionRef).
//
// Composes the kit Section primitive (a semantic <section>). Chrome is plain
// props, merged by the default store `write`: `title`, `description` and
// `size` ("md" or "lg", the preset for the section's look: the space between
// header and body). A hairline between one section and the next is the
// stack that holds them (`divided`), not the section's.
//
// The child at segment "actions" is the header's action area: drawn on the
// right of the title, in a row flow, so a Button or a Row of them sits there
// at its own size. Python names it `section.actions`. Every other child is
// the body, a stack (`layout.tsx`: `gap` 4, `padding`, `justify`, `align`,
// `divided`, the per child maps). The size props sit on the section. No
// header is drawn with no title, description or actions.

import { Section as SectionPrimitive } from "../../components/ui/section";
import {
	ACTIONS_SLOT,
	type NodeEntry,
	type NodeProps,
	SlotView,
	useChildren,
	useEnumProp,
	useStringProp,
} from "../../tree";
import { childHandlers, type LayoutDefaults, Stack, useLayout } from "./layout";

const SIZES = ["md", "lg"] as const;
const SLOTS: ReadonlySet<string> = new Set([ACTIONS_SLOT]);
const DEFAULTS: LayoutDefaults = { gap: 4, justify: "start", align: "stretch" };

function PageSectionView({ path }: NodeProps) {
	const title = useStringProp(path, "title");
	const description = useStringProp(path, "description");
	const size = useEnumProp(path, "size", SIZES, "md");
	const layout = useLayout(path, DEFAULTS);
	const segments = useChildren(path);
	const hasActions = segments.includes(ACTIONS_SLOT);
	const hasBody = segments.some((s) => !SLOTS.has(s));

	return (
		<SectionPrimitive
			size={size}
			title={title || undefined}
			description={description || undefined}
			actions={hasActions ? <SlotView path={path} segment={ACTIONS_SLOT} flow="row" /> : undefined}
			style={layout.size}
		>
			{hasBody ? (
				<Stack
					path={path}
					layout={{ ...layout, size: undefined }}
					slot="section-body"
					skip={SLOTS}
				/>
			) : null}
		</SectionPrimitive>
	);
}

export const PageSection: NodeEntry = {
	component: PageSectionView,
	fill: true,
	handlers: childHandlers,
};
