// Built-in left rail for multi-page nudle apps.
//
// The page list and every label come off the tree: each page node carries
// its route and label as props. A click dispatches a local write to the
// NavRef node, which is what drives pushState and mirrors the new uri, then
// emits a notify so `App.nav.on_change()` subscribers on the server see it.
// Same two steps the old mount-payload version did, minus the payload.

import type { ReactNode } from "react";
import { NavLink, tree, useStringProp } from "@nustackdev/ui-kit";
import { OPS } from "@nustackdev/ui-core";
import { useNavSegment } from "./router";

type Props = {
	appName: string;
	pages: string[];
	active: string | null;
	footer?: ReactNode;
};

function PageLink({
	segment,
	active,
	onGo,
}: {
	segment: string;
	active: boolean;
	onGo: (route: string) => void;
}) {
	const route = useStringProp([segment], "route", `/${segment}`);
	const label = useStringProp([segment], "label", segment);
	return (
		<NavLink
			size="sm"
			active={active}
			onClick={(e) => {
				e.preventDefault();
				onGo(route);
			}}
			href={route}
			className="justify-start w-full"
		>
			{label}
		</NavLink>
	);
}

export function Sidebar({ appName, pages, active, footer }: Props) {
	const nav = useNavSegment();

	const go = (route: string) => {
		if (!nav) return;
		const ref = [nav];
		// Straight into dispatch so NavRef's own write handler runs: it owns
		// pushState, and the mirrored value is what picks the active page.
		tree.getState().dispatch({ op: OPS.write, ref, payload: route });
		tree.getState().send({ op: OPS.notify, ref, payload: route });
	};

	return (
		<aside className="w-52 shrink-0 border-r border-border-default bg-bg-sunken flex flex-col">
			<div className="px-4 py-4 border-b border-border-default">
				<span className="text-xs text-text-muted font-mono uppercase tracking-wider">
					{appName}
				</span>
			</div>
			<nav className="flex-1 overflow-y-auto p-2 flex flex-col gap-0.5">
				{pages.map((segment) => (
					<PageLink key={segment} segment={segment} active={segment === active} onGo={go} />
				))}
			</nav>
			{footer ? <div className="px-4 py-3 border-t border-border-default">{footer}</div> : null}
		</aside>
	);
}
