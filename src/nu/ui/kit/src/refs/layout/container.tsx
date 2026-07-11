// ContainerRef -- layout primitive. Styled box wrapping child Refs.
//
// Display-only, server-owned. One `write` op carries every chrome mutation
// (title, padding, border, background, shadow, gap); payload is a partial
// map. Children are absolute wire paths in the same mount payload; the
// renderer resolves each through the global slice table and dispatches to
// its renderer.

import { ErrorBoundary } from "../../components/ErrorBoundary";
import { renderers } from "../../refs";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const PADDING_CLASSES: Record<string, string> = {
	none: "p-0",
	sm: "p-2",
	md: "p-4",
	lg: "p-6",
};

const BORDER_CLASSES: Record<string, string> = {
	none: "",
	hairline: "border border-border",
	card: "border border-border",
};

const BACKGROUND_CLASSES: Record<string, string> = {
	none: "",
	muted: "bg-muted",
	accent: "bg-accent",
};

const SHADOW_CLASSES: Record<string, string> = {
	none: "",
	sm: "shadow-sm",
	md: "shadow-md",
};

const GAP_CLASSES: Record<string, string> = {
	none: "gap-0",
	sm: "gap-2",
	md: "gap-4",
	lg: "gap-6",
};

const factory: SliceFactory = (path, ctx, props, children) => ({
	type: "Container",
	value: null,
	title: typeof props?.title === "string" ? (props.title as string) : "",
	padding: typeof props?.padding === "string" ? (props.padding as string) : "md",
	border: typeof props?.border === "string" ? (props.border as string) : "hairline",
	background: typeof props?.background === "string" ? (props.background as string) : "none",
	shadow: typeof props?.shadow === "string" ? (props.shadow as string) : "none",
	gap: typeof props?.gap === "string" ? (props.gap as string) : "md",
	children: Array.isArray(children) ? [...children] : [],
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as Record<string, unknown>;
			for (const key of ["title", "padding", "border", "background", "shadow", "gap"]) {
				if (key in p && p[key] != null) {
					slice[key] = String(p[key]);
				}
			}
		}),
});

function ContainerView({ path }: { path: string }) {
	const title = useStore((s) => (s.refs[path]?.title as string) ?? "");
	const padding = useStore((s) => (s.refs[path]?.padding as string) ?? "md");
	const border = useStore((s) => (s.refs[path]?.border as string) ?? "hairline");
	const background = useStore((s) => (s.refs[path]?.background as string) ?? "none");
	const shadow = useStore((s) => (s.refs[path]?.shadow as string) ?? "none");
	const gap = useStore((s) => (s.refs[path]?.gap as string) ?? "md");
	const children = useStore((s) => (s.refs[path]?.children as string[]) ?? []);
	const refs = useStore((s) => s.refs);

	const padCls = PADDING_CLASSES[padding] ?? PADDING_CLASSES.md;
	const borderCls = BORDER_CLASSES[border] ?? BORDER_CLASSES.hairline;
	const bgCls = BACKGROUND_CLASSES[background] ?? "";
	// `card` border bumps the effective minimum shadow to `sm`.
	const effectiveShadow = border === "card" && shadow === "none" ? "sm" : shadow;
	const shadowCls = SHADOW_CLASSES[effectiveShadow] ?? "";
	const gapCls = GAP_CLASSES[gap] ?? GAP_CLASSES.md;

	const boxCls = ["rounded-md", padCls, borderCls, bgCls, shadowCls].filter(Boolean).join(" ");

	return (
		<section className={boxCls}>
			{title ? <h3 className="text-sm font-semibold mb-2">{title}</h3> : null}
			<div className={`flex flex-col ${gapCls}`}>
				{children.map((childPath) => {
					const childSlice = refs[childPath];
					if (!childSlice) {
						return (
							<div key={childPath} className="text-xs text-destructive font-mono">
								no ref at {childPath}
							</div>
						);
					}
					const Comp = renderers[childSlice.type];
					if (!Comp) {
						return (
							<div key={childPath} className="text-xs text-destructive font-mono">
								no renderer for {childSlice.type}
							</div>
						);
					}
					return (
						<ErrorBoundary key={childPath} label={`${childPath} (${childSlice.type})`}>
							<Comp path={childPath} />
						</ErrorBoundary>
					);
				})}
			</div>
		</section>
	);
}

export const Container: RefEntry = { factory, component: ContainerView };
