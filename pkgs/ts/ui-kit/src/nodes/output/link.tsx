// LinkRef -- display-only anchor with href, label, target, and an optional
// external indicator.
//
// Server-owned. A write is a partial merge of {href, label, target, external}
// into the node's props, which is the default store behaviour, so there is no
// handler. The `external` slot is tri-state: true forces the indicator, false
// suppresses it, nil means "auto" (true when target is _blank or the href
// host differs), and that read is done at render time. A plain text link in
// Starlight (content, not navigation), with a lucide ExternalLink glyph.
//
// In a Line (inline flow) it is an inline anchor, not an inline-flex box, so
// a long label wraps with the sentence; the glyph rides the last word.

import { ExternalLink } from "lucide-react";
import { cn } from "../../lib/utils";
import { type NodeEntry, type NodeProps, useFlow, useProp, useStringProp } from "../../tree";

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
	const inline = useFlow() === "inline";
	return (
		<a
			data-slot="link"
			href={href || undefined}
			target={safeTarget}
			rel={rel}
			className={cn(
				inline ? "inline" : "inline-flex items-center gap-1",
				"rounded-sm text-accent-2",
				"underline-offset-2 hover:underline hover:text-accent-2-hover",
				"transition-colors duration-fast ease-out",
				"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
			)}
		>
			<span>{text}</span>
			{showExternal ? (
				<ExternalLink
					aria-hidden="true"
					className={cn("size-3.5 shrink-0", inline && "ms-1 inline align-[-0.125em]")}
				/>
			) : null}
		</a>
	);
}

export const LinkRef: NodeEntry = { component: LinkView };
