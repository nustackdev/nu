// The nudle shell.
//
// Everything on screen is a node in the tree. The shell picks the active
// page and renders it; the rest is chrome. Structural nodes (TitleRef,
// NavRef) render null but have to mount, because their effects are the
// whole point of them, so they stay in the tree outside the body flow.

import { Badge, NodeChildren, NodeView, useBoolProp, useStringProp } from "@nustackdev/ui-kit";
import type { Path } from "@nustackdev/ui-core";
import "./nodes";
import { useNudleConnection } from "./connect";
import { useActivePage, usePageSegments, useRootSegments } from "./router";
import { Sidebar } from "./Sidebar";

const ROOT: Path = [];

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

	const { label, variant } = statusConfig[status];
	const statusBadge = <Badge variant={variant}>{label}</Badge>;
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
	const waiting = <p className="text-sm text-muted-foreground font-mono">waiting for the tree...</p>;

	if (sidebarOn && pages.length > 1) {
		return (
			<div className="h-screen flex overflow-hidden">
				{chromeNodes}
				<Sidebar appName={appName} pages={pages} active={active} footer={statusBadge} />
				<main className="flex-1 min-w-0 h-full overflow-y-auto overflow-x-auto">
					<div className="mx-auto max-w-5xl p-6">{booted ? body : waiting}</div>
				</main>
			</div>
		);
	}

	return (
		<div className="min-h-screen p-6">
			<div className="mx-auto max-w-3xl">
				<div className="mb-4 flex items-center justify-between">
					<span className="text-sm text-muted-foreground font-mono">nudle</span>
					{statusBadge}
				</div>
				{chromeNodes}
				{booted ? body : waiting}
			</div>
		</div>
	);
}

export default App;
