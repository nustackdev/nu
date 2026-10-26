// Anchors: the one way the kit turns an href and a target into a real <a>.
//
// Every navigating control (a link button, a link card, a page link, a nav
// item, a breadcrumb, an empty state's way out) is a real anchor, so
// cmd-click, copy link and a host's AnchorCatcher (../tree/anchors) all work. `anchorProps` is the
// attribute set they share: only `_blank` opens elsewhere, and it always
// carries `noopener noreferrer`. Anything else is the page's own tab.
//
// `resolveHref` reads an href against the page, for the two questions a
// control asks of one: is it this app (`sameOrigin`, what a nav item may be
// active for) and is it another site (`crossHost`, what earns the external
// glyph). An empty or unparseable href is neither.

export type AnchorTarget = "_self" | "_blank";

export type AnchorProps = {
	href: string | undefined;
	target: "_blank" | undefined;
	rel: "noopener noreferrer" | undefined;
};

/** `_blank` or the page's own tab; anything off the wire that is not `_blank` stays. */
export function normTarget(target: string | null | undefined): AnchorTarget {
	return target === "_blank" ? "_blank" : "_self";
}

/** The <a> attributes for `href` and `target`. An empty href is no href. */
export function anchorProps(href: string, target?: string | null): AnchorProps {
	const blank = normTarget(target) === "_blank";
	return {
		href: href === "" ? undefined : href,
		target: blank ? "_blank" : undefined,
		rel: blank ? "noopener noreferrer" : undefined,
	};
}

/** `href` resolved against the page, or null for an empty or unparseable one. */
export function resolveHref(href: string): URL | null {
	if (href === "") return null;
	try {
		return new URL(href, window.location.href);
	} catch {
		return null;
	}
}

/** Whether `href` is a page of this app: same origin as the page. */
export function sameOrigin(href: string): boolean {
	const url = resolveHref(href);
	return url !== null && url.origin === window.location.origin;
}

/** Whether `href` names another host, the case a link marks as external. */
export function crossHost(href: string): boolean {
	const url = resolveHref(href);
	return url !== null && url.host !== "" && url.host !== window.location.host;
}
