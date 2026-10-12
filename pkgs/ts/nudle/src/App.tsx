// The nudle shell.
//
// Everything on screen is a node in the tree. The shell picks the active
// page and renders it; the rest is chrome. Structural nodes (TitleRef,
// NavRef) render null but have to mount, because their effects are the
// whole point of them, so they stay in the tree outside the body flow.
//
// With a sidebar the page sits in the kit's split (`ResizablePanelGroup`):
// the sidebar is a collapsible panel with the kit's sidebar bounds and a px
// default, so it holds its width while the window resizes. Drag its border
// to resize it, past its minimum to fold it; Enter on the border, the
// sidebar's button, the button over the page and cmd/ctrl+\ fold and unfold
// it too. The split keeps the layout across reloads, as nuspace's does.

import {
	Badge,
	cn,
	NodeChildren,
	NodeView,
	ResizableHandle,
	ResizablePanel,
	ResizablePanelGroup,
	type ResizablePanelGroupHandle,
	SIDEBAR_WIDTH,
	useBoolProp,
	useStringProp,
} from "@nustackdev/ui-kit";
import type { Path } from "@nustackdev/ui-core";
import { type RefObject, useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import "./nodes";
import { useNudleConnection } from "./connect";
import { useActivePage, usePageSegments, useRootSegments } from "./router";
import { Sidebar, SidebarToggle } from "./Sidebar";
import { ThemeToggle } from "./theme";

const ROOT: Path = [];

/** Where the split keeps the sidebar's width and fold. */
const SIDEBAR_LAYOUT_KEY = "nudle.sidebar.layout";

/**
 * The sidebar's fold, read off the split, and a flip that asks the split.
 * Cmd/ctrl+\ flips it from anywhere, and a flip by a button moves focus to
 * the button that undoes it, so a keyboard user is not dropped on the body.
 */
function useSidebarFold(split: RefObject<ResizablePanelGroupHandle | null>, shown: boolean) {
	const [folded, setFolded] = useState(false);
	// The split mounts once the pages land: read its fold as it does.
	useLayoutEffect(() => setFolded(split.current?.isCollapsed(0) ?? false), [shown]);

	const flip = useCallback(
		(fold: boolean) => {
			const g = split.current;
			if (!g) return;
			if (fold) g.collapse(0);
			else g.expand(0);
		},
		[split],
	);

	const flipAndFocus = useCallback(
		(fold: boolean) => {
			flip(fold);
			requestAnimationFrame(() => {
				for (const el of document.querySelectorAll<HTMLElement>("[data-sidebar-toggle]")) {
					if (!el.closest("[inert]")) return el.focus();
				}
			});
		},
		[flip],
	);

	useEffect(() => {
		const onKey = (e: KeyboardEvent) => {
			if (e.key !== "\\" || !(e.metaKey || e.ctrlKey) || e.altKey || e.shiftKey) return;
			e.preventDefault();
			flip(!(split.current?.isCollapsed(0) ?? false));
		};
		window.addEventListener("keydown", onKey);
		return () => window.removeEventListener("keydown", onKey);
	}, [flip, split]);

	/** For the split's `onLayout`: the sidebar is panel 0. */
	const onLayout = useCallback((sizes: number[]) => setFolded(sizes[0] <= 0), []);

	return { folded, flipAndFocus, onLayout };
}

const statusConfig = {
	connecting: { label: "connecting", variant: "outline" as const },
	connected: { label: "connected", variant: "default" as const },
	reconnecting: { label: "reconnecting...", variant: "outline" as const },
	disconnected: { label: "disconnected", variant: "danger" as const },
};

function App() {
	const status = useNudleConnection();
	const appName = useStringProp(ROOT, "name", "nudle");
	const sidebarOn = useBoolProp(ROOT, "sidebar");
	const rootSegments = useRootSegments();
	const pages = usePageSegments();
	const active = useActivePage();
	const withSidebar = sidebarOn && pages.length > 1;
	const split = useRef<ResizablePanelGroupHandle | null>(null);
	const { folded, flipAndFocus, onLayout } = useSidebarFold(split, withSidebar);

	const { label, variant } = statusConfig[status];
	const statusBadge = (
		<div className="flex items-center gap-2">
			<Badge variant={variant}>{label}</Badge>
			<ThemeToggle />
		</div>
	);
	const booted = rootSegments.length > 0;

	// With pages, the body is the active one and everything else at the root
	// is chrome. Without, the root's children are the whole surface.
	const chrome = active ? rootSegments.filter((s) => !pages.includes(s)) : [];
	const chromeNodes = chrome.map((segment) => <NodeView key={segment} path={[segment]} />);
	const body = active ? (
		<NodeView path={[active]} />
	) : (
		<div className="flex flex-col gap-6">
			<NodeChildren path={ROOT} />
		</div>
	);
	const waiting = <p className="text-sm text-text-muted font-mono">waiting for the tree...</p>;

	if (withSidebar) {
		return (
			<div className="h-screen flex overflow-hidden bg-[var(--ground-raised)]">
				{chromeNodes}
				<ResizablePanelGroup ref={split} storageKey={SIDEBAR_LAYOUT_KEY} onLayout={onLayout}>
					<ResizablePanel
						id="nudle-sidebar"
						defaultSize={`${SIDEBAR_WIDTH.DEFAULT}px`}
						minSize={`${SIDEBAR_WIDTH.MIN}px`}
						maxSize={`${SIDEBAR_WIDTH.MAX}px`}
						collapsible
						className="flex"
					>
						<Sidebar
							appName={appName}
							pages={pages}
							active={active}
							footer={statusBadge}
							onHide={() => flipAndFocus(true)}
						/>
					</ResizablePanel>
					<ResizableHandle aria-label="Resize sidebar" />
					<ResizablePanel id="nudle-page" className="flex">
						{/* Pinned over the page, outside the scroller, so it stays put and never shifts the content. */}
						{folded ? (
							<div className="absolute top-3 left-3 z-10">
								<SidebarToggle label="Show sidebar" onClick={() => flipAndFocus(false)} />
							</div>
						) : null}
						<main className="flex-1 min-w-0 h-full overflow-y-auto overflow-x-auto">
							{/* Folded, the gutter clears the pinned button on a narrow window. */}
							<div className={cn("mx-auto max-w-5xl p-6", folded && "px-14")}>
								{booted ? body : waiting}
							</div>
						</main>
					</ResizablePanel>
				</ResizablePanelGroup>
			</div>
		);
	}

	return (
		<div className="min-h-screen p-6 bg-[var(--ground-raised)]">
			<div className="mx-auto max-w-3xl">
				<div className="mb-4 flex items-center justify-between">
					<span className="text-sm text-text-muted font-mono">nudle</span>
					{statusBadge}
				</div>
				{chromeNodes}
				{booted ? body : waiting}
			</div>
		</div>
	);
}

export default App;
