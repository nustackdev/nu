// CardRef -- card-styled Section. Header (title + subtitle), body
// (vertical stack of child Refs), footer (plain text). Display-only,
// server-owned. Three dedicated ops carry chrome mutations:
// `store_title`, `store_subtitle`, `store_footer`; each takes a string
// (nil coerces to ""). Children are absolute wire paths supplied by the
// mount walker; the renderer resolves each through the global slice
// table and dispatches to its renderer.

import { ErrorBoundary } from "@/components/ErrorBoundary";
import { renderers } from "../refs";
import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

function coerceStr(v: unknown): string {
	return v == null ? "" : String(v);
}

const factory: SliceFactory = (path, ctx, props, children) => ({
	type: "CardRef",
	value: null,
	title: typeof props?.title === "string" ? (props.title as string) : "",
	subtitle: typeof props?.subtitle === "string" ? (props.subtitle as string) : "",
	footer: typeof props?.footer === "string" ? (props.footer as string) : "",
	children: Array.isArray(children) ? [...children] : [],
	store_title: (v: unknown) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			slice.title = coerceStr(v);
		}),
	store_subtitle: (v: unknown) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			slice.subtitle = coerceStr(v);
		}),
	store_footer: (v: unknown) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			slice.footer = coerceStr(v);
		}),
});

function CardView({ path }: { path: string }) {
	const title = useStore((s) => (s.refs[path]?.title as string) ?? "");
	const subtitle = useStore((s) => (s.refs[path]?.subtitle as string) ?? "");
	const footer = useStore((s) => (s.refs[path]?.footer as string) ?? "");
	const childPaths = useStore((s) => (s.refs[path]?.children as string[]) ?? []);
	const refs = useStore((s) => s.refs);

	const showHeader = title !== "" || subtitle !== "";

	return (
		<section className="rounded-md border bg-card text-card-foreground shadow-sm">
			{showHeader ? (
				<header className="px-4 pt-4 pb-2">
					{title !== "" ? <h3 className="text-sm font-semibold">{title}</h3> : null}
					{subtitle !== "" ? <p className="text-xs text-muted-foreground">{subtitle}</p> : null}
				</header>
			) : null}
			<div className="flex flex-col gap-3 px-4 py-3">
				{childPaths.map((cp) => {
					const childSlice = refs[cp];
					if (!childSlice) {
						return (
							<div key={cp} className="text-xs text-destructive font-mono">
								no ref at {cp}
							</div>
						);
					}
					const Comp = renderers[childSlice.type];
					if (!Comp) {
						return (
							<div key={cp} className="text-xs text-destructive font-mono">
								no renderer for {childSlice.type}
							</div>
						);
					}
					return (
						<ErrorBoundary key={cp} label={`${cp} (${childSlice.type})`}>
							<Comp path={cp} />
						</ErrorBoundary>
					);
				})}
			</div>
			{footer !== "" ? (
				<footer className="px-4 py-2 border-t text-xs text-muted-foreground">{footer}</footer>
			) : null}
		</section>
	);
}

export const CardRef: RefEntry = { factory, component: CardView };
