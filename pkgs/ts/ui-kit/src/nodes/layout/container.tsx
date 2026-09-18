// Container -- styled box wrapping other nodes. Title, padding, border,
// background, shadow and gap are plain props; the default store `write`
// merges them, and the read-time fallbacks below match what the old factory
// seeded, so there is no handler here.
//
// Children are the node's own children in the tree; `NodeChildren` resolves
// and renders each one. Composes the kit Panel primitive; the
// background/border grid collapses onto Panel variants + semantic tone
// classes.

import { Panel, PanelContent, PanelHeader, PanelTitle } from "../../components/ui/panel";
import { NodeChildren, type NodeEntry, type NodeProps, useStringProp } from "../../tree";

const PADDING_TO_SIZE: Record<string, "sm" | "md" | "lg"> = {
	none: "sm",
	sm: "sm",
	md: "md",
	lg: "lg",
};

const GAP_CLASSES: Record<string, string> = {
	none: "gap-0",
	sm: "gap-2",
	md: "gap-4",
	lg: "gap-6",
};

// background maps: `accent` (previously a solid) reads better as the accent
// wash, per palette.md §2.4; solid accents belong on interactive surfaces.
const BACKGROUND_CLASSES: Record<string, string> = {
	none: "",
	muted: "bg-bg-sunken",
	accent: "bg-accent-wash",
};

const SHADOW_CLASSES: Record<string, string> = {
	none: "",
	sm: "shadow-sm",
	md: "shadow-md",
};

function ContainerView({ path }: NodeProps) {
	const title = useStringProp(path, "title");
	const padding = useStringProp(path, "padding", "md");
	const border = useStringProp(path, "border", "hairline");
	const background = useStringProp(path, "background", "none");
	const shadow = useStringProp(path, "shadow", "none");
	const gap = useStringProp(path, "gap", "md");

	const size = PADDING_TO_SIZE[padding] ?? "md";
	const gapCls = GAP_CLASSES[gap] ?? GAP_CLASSES.md;
	const bgCls = BACKGROUND_CLASSES[background] ?? "";
	// `card` border bumps the effective minimum shadow to `sm`.
	const effectiveShadow = border === "card" && shadow === "none" ? "sm" : shadow;
	const shadowCls = SHADOW_CLASSES[effectiveShadow] ?? "";
	const borderCls = border === "none" ? "border-none" : "";

	return (
		<Panel size={size} className={`${bgCls} ${shadowCls} ${borderCls}`.trim()}>
			{title ? (
				<PanelHeader>
					<PanelTitle>{title}</PanelTitle>
				</PanelHeader>
			) : null}
			<PanelContent>
				<div className={`flex flex-col ${gapCls}`}>
					<NodeChildren path={path} />
				</div>
			</PanelContent>
		</Panel>
	);
}

export const Container: NodeEntry = { component: ContainerView };
