// Built-in left rail for multi-page nudle apps.
//
// The page list and every label come off the tree: each page node carries
// its route and label as props. Picking a page is a push through the kit's
// History, the one writer of browser history. The router hears it and shows
// the page; a HistoryRef the app mounts hears it too and tells the server.
// The sidebar needs neither: it works the same with no HistoryRef at all.
//
// The rail fills the split panel App puts it in: the panel owns the width
// and the fold. The header's button hides it, as nuspace's does, and
// `SidebarToggle` is the same button over the page to bring it back.

import { type ReactNode, useMemo, useRef } from "react";
import {
	History,
	IconButton,
	Shortcut,
	Tooltip,
	TooltipContent,
	TooltipProvider,
	TooltipTrigger,
	Tree,
	TreeItem,
	type TreeItemState,
	type TreeSource,
	useStringProp,
} from "@nustackdev/ui-kit";
import { routeOf } from "./router";

type Props = {
	appName: string;
	pages: string[];
	active: string | null;
	footer?: ReactNode;
	/** Fold the sidebar away. */
	onHide: () => void;
};

/** The hide / show shortcut, as kit `Shortcut` key names: cmd/ctrl+\. */
export const SIDEBAR_KEYS = ["mod", "\\"] as const;

/** lucide panel-left, inline like the page glyph. */
function PanelGlyph() {
	return (
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
			<rect width="18" height="18" x="3" y="3" rx="2" />
			<path d="M9 3v18" />
		</svg>
	);
}

/**
 * The panel-left button: in the sidebar's header, and over the page while the
 * sidebar is folded. `data-sidebar-toggle` is how App finds the one to focus
 * after a flip.
 */
export function SidebarToggle({ label, onClick }: { label: string; onClick: () => void }) {
	return (
		<TooltipProvider>
			<Tooltip>
				<TooltipTrigger asChild>
					<IconButton
						variant="ghost"
						size="sm"
						aria-label={label}
						data-sidebar-toggle=""
						onClick={onClick}
					>
						<PanelGlyph />
					</IconButton>
				</TooltipTrigger>
				<TooltipContent side="bottom">
					{label}
					<Shortcut keys={SIDEBAR_KEYS} size="sm" />
				</TooltipContent>
			</Tooltip>
		</TooltipProvider>
	);
}

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
	const route = routeOf(segment, useStringProp([segment], "route"));
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

export function Sidebar({ appName, pages, active, footer, onHide }: Props) {
	const routes = useRef(new Map<string, string>()).current;
	const source = useMemo<TreeSource>(() => ({ roots: pages, childrenOf: () => [] }), [pages]);

	const go = (route: string) => {
		History.push(route);
	};

	return (
		<aside className="relative flex min-w-0 flex-1 flex-col bg-bg-sunken">
			<div className="flex items-center gap-1 px-2 pt-3 pb-2">
				<SidebarToggle label="Hide sidebar" onClick={onHide} />
				<span className="truncate text-sm font-semibold text-text-primary">
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
					onSelect={(key) => go(routes.get(key) ?? routeOf(key, null))}
					selectionFollowsFocus={false}
					renderItem={(item) => <PageItem item={item} routes={routes} />}
				/>
			</nav>
			{footer ? <div className="px-4 py-3">{footer}</div> : null}
		</aside>
	);
}
