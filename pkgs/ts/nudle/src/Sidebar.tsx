// Built-in left rail for multi-page nudle apps.
//
// The page list and every label come off the tree: each page node carries
// its route and label as props. A click dispatches a local write to the
// NavRef node, which is what drives pushState and mirrors the new uri, then
// emits a notify so `App.nav.on_change()` subscribers on the server see it.
// Same two steps the old mount-payload version did, minus the payload.

import { type ReactNode, useMemo, useRef } from "react";
import {
	ResizeHandle,
	Tree,
	TreeItem,
	type TreeItemState,
	type TreeSource,
	tree,
	useResizableWidth,
	useStringProp,
} from "@nustackdev/ui-kit";
import { OPS } from "@nustackdev/ui-core";
import { useNavSegment } from "./router";

type Props = {
	appName: string;
	pages: string[];
	active: string | null;
	footer?: ReactNode;
};

// The pages are a flat tree: every page is a root, nothing folds. The kit's
// Tree gives the rows, the keyboard and the selected wash the same as
// nuspace's sidebar.
const NOTHING_OPEN: ReadonlySet<string> = new Set();
const noFold = () => {};

// A page with no `icon` prop gets a plain page glyph (lucide file-text), so
// every row keeps the same icon lane as nuspace's planes.
function PageGlyph() {
	return (
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
			<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
			<path d="M14 2v4a2 2 0 0 0 2 2h4" />
			<path d="M10 9H8" />
			<path d="M16 13H8" />
			<path d="M16 17H8" />
		</svg>
	);
}

function PageItem({ item, routes }: { item: TreeItemState; routes: Map<string, string> }) {
	const segment = item.row.key;
	const route = useStringProp([segment], "route", `/${segment}`);
	const label = useStringProp([segment], "label", segment);
	const icon = useStringProp([segment], "icon", "");
	routes.set(segment, route);
	return (
		<TreeItem
			item={item}
			title={label}
			icon={icon ? <span className="text-base leading-none">{icon}</span> : <PageGlyph />}
		/>
	);
}

export function Sidebar({ appName, pages, active, footer }: Props) {
	const nav = useNavSegment();
	// Drag the edge to resize, click it to snap back. Same bounds as nuspace.
	const { width, onResizeStart, onResizeReset } = useResizableWidth("nudle.sidebar.width");

	const routes = useRef(new Map<string, string>()).current;
	const source = useMemo<TreeSource>(() => ({ roots: pages, childrenOf: () => [] }), [pages]);

	const go = (route: string) => {
		if (!nav) return;
		const ref = [nav];
		// Straight into dispatch so NavRef's own write handler runs: it owns
		// pushState, and the mirrored value is what picks the active page.
		tree.getState().dispatch({ op: OPS.write, ref, payload: route });
		tree.getState().send({ op: OPS.notify, ref, payload: route });
	};

	return (
		<aside
			className="relative shrink-0 border-r border-border-subtle bg-bg-sunken flex flex-col"
			style={{ width }}
		>
			<div className="px-4 pt-4 pb-2">
				<span className="text-sm font-semibold text-text-primary">
					{appName}
				</span>
			</div>
			<nav className="flex-1 overflow-y-auto p-2">
				<Tree
					aria-label="Pages"
					source={source}
					expanded={NOTHING_OPEN}
					onToggle={noFold}
					selectedKey={active}
					onSelect={(key) => go(routes.get(key) ?? `/${key}`)}
					selectionFollowsFocus={false}
					renderItem={(item) => <PageItem item={item} routes={routes} />}
				/>
			</nav>
			{footer ? <div className="px-4 py-3">{footer}</div> : null}
			<ResizeHandle onPointerDown={onResizeStart} onDoubleClick={onResizeReset} />
		</aside>
	);
}
