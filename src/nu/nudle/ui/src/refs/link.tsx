// LinkRef -- display-only anchor with href, label, target, and an optional
// external indicator.
//
// Server-owned. One `write` op carries every mutation; payload is a partial
// map so missing keys leave the slice value untouched. Class-level defaults
// come in on the mount field `props` and seed the slice. The `external` slot
// is tri-state: true forces the indicator, false suppresses it, null means
// "auto" (true when target is _blank or the href host differs).

import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

function normalizeTarget(v: unknown): "_self" | "_blank" {
	return v === "_blank" ? "_blank" : "_self";
}

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

const factory: SliceFactory = (path, ctx, props) => ({
	type: "LinkRef",
	value: null,
	href: typeof props?.href === "string" ? (props.href as string) : "",
	label: typeof props?.label === "string" ? (props.label as string) : "",
	target: normalizeTarget(props?.target),
	external: normalizeExternal(props?.external),
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as {
				href?: unknown;
				label?: unknown;
				target?: unknown;
				external?: unknown;
			};
			if ("href" in p) {
				slice.href = p.href == null ? "" : String(p.href);
			}
			if ("label" in p) {
				slice.label = p.label == null ? "" : String(p.label);
			}
			if ("target" in p) {
				slice.target = p.target == null ? "_self" : normalizeTarget(p.target);
			}
			if ("external" in p) {
				slice.external = normalizeExternal(p.external);
			}
		}),
});

function LinkView({ path }: { path: string }) {
	const href = useStore((s) => (s.refs[path]?.href as string) ?? "");
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const target = useStore((s) => (s.refs[path]?.target as string) ?? "_self");
	const external = useStore((s) => s.refs[path]?.external as boolean | null | undefined);
	const safeTarget = target === "_blank" ? "_blank" : "_self";
	const showExternal =
		external === true || (external == null && (safeTarget === "_blank" || isCrossHost(href)));
	const text = label !== "" ? label : href;
	const rel = safeTarget === "_blank" ? "noopener noreferrer" : undefined;
	return (
		<a
			href={href || undefined}
			target={safeTarget}
			rel={rel}
			className="text-blue-600 hover:underline"
		>
			{text}
			{showExternal ? (
				<span aria-hidden="true" className="ml-0.5">
					{"↗"}
				</span>
			) : null}
		</a>
	);
}

export const LinkRef: RefEntry = { factory, component: LinkView };
