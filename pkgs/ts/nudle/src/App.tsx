// The nudle shell.
//
// nudle decides nothing. The program draws the whole tree (pages, navs, the
// title and the History included) and the shell renders the root's children
// in the order they reached the tree. Structural nodes (TitleRef, HistoryRef)
// render null but mount like the rest, because their effects are the whole
// point of them. What shows for a URL is the program's call too: it listens
// to its HistoryRef and draws the branch (`nustd.ui.route` in Python), so a
// page switch is a round trip.
//
// The whole shell sits in the kit's AnchorCatcher with its default rule, so a
// plain click on any same-origin link (a LinkRef, a ButtonRef with an href, a
// NavItem, a markdown link) is a History push, not a page load that drops
// the socket. Cmd-click and the rest stay the browser's.
//
// Besides the tree, the shell keeps only what is about the socket: a compact
// header on the sidebar's ground (`ground-deep`, a `line-subtle` hairline)
// with the connection badge and the theme toggle, and "waiting for the
// tree..." until the first node lands. Below it the main area is the page
// background and the root's children drawn bare: no flow, no gap, no width
// cap, no padding. A program frames its content itself, in a Container, and
// a headless node at the root (TitleRef, HistoryRef) takes no space.

import {
	AnchorCatcher,
	BareCell,
	Container,
	NodeChildren,
	Skeleton,
	StatusPill,
	useTree,
} from "@nustackdev/ui-kit";
import type { Path } from "@nustackdev/ui-core";
import { type Status, useNudleConnection } from "./connect";
import nuMark from "./nu-mark.svg";
import { ThemeToggle } from "./theme";

const ROOT: Path = [];

const statusConfig = {
	connecting: { label: "connecting", tone: "info" as const },
	connected: { label: "connected", tone: "ok" as const },
	reconnecting: { label: "reconnecting...", tone: "warn" as const },
	disconnected: { label: "disconnected", tone: "danger" as const },
};

/**
 * What the main area holds until the program's first node lands: the outline
 * of a page (a heading, a line of text, two cards) in the default page frame,
 * pulsing. Says "Booting" to a screen reader.
 */
function Booting() {
	return (
		<Container data-slot="nudle-booting" role="status" aria-live="polite" className="gap-6">
			<span className="sr-only">Booting</span>
			<div className="flex flex-col gap-3">
				<Skeleton className="h-8 w-56" />
				<Skeleton shape="text" className="w-2/3" />
			</div>
			<Skeleton className="h-36 w-full rounded-lg" />
			<Skeleton className="h-56 w-full rounded-lg" />
		</Container>
	);
}

/** The shell around the tree, for a connection in `status`. */
export function Shell({ status }: { status: Status }) {
	const booted = useTree((s) => s.root.children.size > 0);
	const { label, tone } = statusConfig[status];
	return (
		<AnchorCatcher>
			<div className="min-h-screen bg-[var(--ground-raised)]">
				<header
					data-slot="nudle-header"
					className="h-10 border-b border-[var(--line-subtle)] bg-[var(--ground-deep)]"
				>
					{/* The bar runs edge to edge; what is on it stops at the main
					    width, on the page gutter, so it lines up with a page below. */}
					<Container size="main" className="h-full flex-row items-center justify-between">
						<span className="flex items-center gap-2">
							<img src={nuMark} alt="" className="size-5" />
							<span className="text-sm text-text-muted font-mono">nudle</span>
						</span>
						<div className="flex items-center gap-2">
							<StatusPill tone={tone} size="sm">
								{label}
							</StatusPill>
							<ThemeToggle />
						</div>
					</Container>
				</header>
				<main data-slot="nudle-main" className="py-6">
					{booted ? (
						<NodeChildren path={ROOT} cell={BareCell} />
					) : (
						<Booting />
					)}
				</main>
			</div>
		</AnchorCatcher>
	);
}

function App() {
	return <Shell status={useNudleConnection()} />;
}

export default App;
