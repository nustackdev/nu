// Built-in left rail for multi-page nudle apps.
//
// Reads the mounted `pages` list and the NavRef's current value from the
// store. A click writes to the NavRef slice locally (pushState + zustand
// mirror) and emits a notify frame so any server-side
// `App.nav.changed()` subscribers observe the change.

import type { ReactNode } from "react";
import { NavLink, useStore } from "@nustackdev/ui-kit";
import { OP_NOTIFY, type MountField, type MountPage } from "@nustackdev/ui-core";

function findNavPath(fields: MountField[]): string | null {
	for (const f of fields) {
		if (f.type === "NavRef") return f.path;
	}
	return null;
}

type Props = {
	indexName: string;
	pages: MountPage[];
	structural: MountField[];
	footer?: ReactNode;
};

export function Sidebar({ indexName, pages, structural, footer }: Props) {
	const navPath = findNavPath(structural);
	const currentUri = useStore((s) =>
		navPath ? (s.refs[navPath]?.value as string | undefined) : undefined,
	);

	const go = (route: string) => {
		if (!navPath) return;
		const slice = useStore.getState().refs[navPath];
		slice?.write?.(route);
		useStore.getState().send({ op: OP_NOTIFY, ref: navPath, payload: route });
	};

	// Fallback active is the first page (mirrors router.ts).
	const active = currentUri ?? pages[0]?.route;

	return (
		<aside className="w-52 shrink-0 border-r border-border-default bg-bg-sunken flex flex-col">
			<div className="px-4 py-4 border-b border-border-default">
				<span className="text-xs text-text-muted font-mono uppercase tracking-wider">
					{indexName}
				</span>
			</div>
			<nav className="flex-1 overflow-y-auto p-2 flex flex-col gap-0.5">
				{pages.map((p) => (
					<NavLink
						key={p.route}
						size="sm"
						active={p.route === active}
						onClick={(e) => {
							e.preventDefault();
							go(p.route);
						}}
						href={p.route}
						className="justify-start w-full"
					>
						{p.label}
					</NavLink>
				))}
			</nav>
			{footer ? (
				<div className="px-4 py-3 border-t border-border-default">{footer}</div>
			) : null}
		</aside>
	);
}
