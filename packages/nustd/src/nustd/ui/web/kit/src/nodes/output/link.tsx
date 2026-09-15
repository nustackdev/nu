// LinkRef -- display-only anchor with href, label, target, and an optional
// external indicator.
//
// Server-owned. A write is a partial merge of {href, label, target, external}
// into the node's props, which is the default store behaviour, so there is no
// handler. The `external` slot is tri-state: true forces the indicator, false
// suppresses it, nil means "auto" (true when target is _blank or the href
// host differs), and that read is done at render time. Composes the kit
// NavLink primitive with a lucide ExternalLink glyph.

import { ExternalLink } from "lucide-react";
import { NavLink } from "../../components/ui/nav-link";
import { type NodeEntry, type NodeProps, useProp, useStringProp } from "../../tree";

function normalizeExternal(v: unknown): boolean | null {
	if (v === true) return true;
	if (v === false) return false;
	return null;
}

function isCrossHost(href: string): boolean {
	if (href === "") return false;
	try {
		const url = new URL(href, window.location.href);
		return url.host !== "" && url.host !== window.location.host;
	} catch {
		return false;
	}
}

function LinkView({ path }: NodeProps) {
	const href = useStringProp(path, "href");
	const label = useStringProp(path, "label");
	const target = useStringProp(path, "target", "_self");
	const external = normalizeExternal(useProp<unknown>(path, "external", null));
	const safeTarget = target === "_blank" ? "_blank" : "_self";
	const showExternal =
		external === true || (external == null && (safeTarget === "_blank" || isCrossHost(href)));
	const text = label !== "" ? label : href;
	const rel = safeTarget === "_blank" ? "noopener noreferrer" : undefined;
	return (
		<NavLink
			variant="underline"
			href={href || undefined}
			target={safeTarget}
			rel={rel}
			className="text-accent-2 hover:text-accent-2-hover"
		>
			<span>{text}</span>
			{showExternal ? <ExternalLink aria-hidden="true" className="size-3.5" /> : null}
		</NavLink>
	);
}

export const LinkRef: NodeEntry = { component: LinkView };
