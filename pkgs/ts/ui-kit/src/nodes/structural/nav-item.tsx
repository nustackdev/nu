// NavItemRef -- one link in a sidebar or a top bar, aware of where the tab is.
//
// Server-owned, plain props merged by the default store `write`: `label`,
// `href`, `target` ("_self" or "_blank"), `icon` (a curated lucide name, see
// ../input/icons), `meta` (a trailing note: a count, a shortcut), `active`
// and `exact`. Composes the kit NavLink primitive, a real <a href> drawn
// through `anchorProps` like every kit link, so a host's AnchorCatcher routes
// it and the browser's own link handling is untouched.
//
// `active` true or false is what it says. Unset (nil) it follows the tab:
// active while the location's pathname is the href's, or under it ("/docs"
// is active on "/docs/intro") unless `exact` is set. "/" only ever matches
// itself, or it would be active everywhere. A cross-origin href is never
// auto-active. The matcher is the kit's one, `matchesPath`.
//
// Where the tab is comes from History (`usePathname` in ../../tree/history),
// which hears every move the page makes.
//
// Drawn per flow: in a block flow (a vertical NavList, a Column) the item
// is a full width row with its label at the start; in a row flow (a
// horizontal NavList, a Row) it keeps its own width.

import { NavLink } from "../../components/ui/nav-link";
import { anchorProps } from "../../lib/anchor";
import { cn } from "../../lib/utils";
import {
	matchesPath,
	type NodeEntry,
	type NodeProps,
	useFlow,
	usePathname,
	useProp,
	useStringProp,
} from "../../tree";
import { iconFor } from "../input/icons";

function NavItemView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const href = useStringProp(path, "href");
	const target = useStringProp(path, "target", "_self");
	const iconName = useStringProp(path, "icon");
	const meta = useStringProp(path, "meta");
	const active = useProp<unknown>(path, "active", null);
	const exact = useProp<unknown>(path, "exact", false) === true;
	const pathname = usePathname();
	const block = useFlow() === "block";
	const Icon = iconFor(iconName);
	const isActive =
		active === true || (active !== false && active == null && matchesPath(href, pathname, exact));
	return (
		<NavLink
			{...anchorProps(href, target)}
			active={isActive}
			className={cn(block ? "w-full justify-start" : "shrink-0")}
		>
			{Icon ? <Icon aria-hidden /> : null}
			<span className="min-w-0 truncate">{label === "" ? href : label}</span>
			{meta !== "" ? (
				<span data-slot="nav-item-meta" className="ms-auto ps-2 text-xs text-text-muted">
					{meta}
				</span>
			) : null}
		</NavLink>
	);
}

export const NavItemRef: NodeEntry = { component: NavItemView };
