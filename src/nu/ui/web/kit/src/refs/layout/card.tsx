// Card -- card-styled Section. Header (title + subtitle), body
// (vertical stack of child Refs), footer (plain text). Display-only,
// server-owned. Three dedicated ops carry chrome mutations:
// `set_title`, `set_subtitle`, `set_footer`; each takes a string
// (nil coerces to ""). Children are absolute wire paths supplied by the
// mount walker; the renderer resolves each through the global slice
// table and dispatches to its renderer. Composes the kit Card primitive
// family.

import { ErrorBoundary } from "../../components/ErrorBoundary";
import {
	Card as CardPrimitive,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from "../../components/ui/card";
import { renderers } from "../../refs";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

function coerceStr(v: unknown): string {
	return v == null ? "" : String(v);
}

const factory: SliceFactory = (path, ctx, props, children) => ({
	type: "Card",
	value: null,
	title: typeof props?.title === "string" ? (props.title as string) : "",
	subtitle: typeof props?.subtitle === "string" ? (props.subtitle as string) : "",
	footer: typeof props?.footer === "string" ? (props.footer as string) : "",
	children: Array.isArray(children) ? [...children] : [],
	set_title: (v: unknown) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			slice.title = coerceStr(v);
		}),
	set_subtitle: (v: unknown) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			slice.subtitle = coerceStr(v);
		}),
	set_footer: (v: unknown) =>
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
		<CardPrimitive>
			{showHeader ? (
				<CardHeader>
					{title !== "" ? <CardTitle>{title}</CardTitle> : null}
					{subtitle !== "" ? <CardDescription>{subtitle}</CardDescription> : null}
				</CardHeader>
			) : null}
			<CardContent className="flex flex-col gap-3 py-3">
				{childPaths.map((cp) => {
					const childSlice = refs[cp];
					if (!childSlice) {
						return (
							<div key={cp} className="text-xs text-status-danger font-mono">
								no ref at {cp}
							</div>
						);
					}
					const Comp = renderers[childSlice.type];
					if (!Comp) {
						return (
							<div key={cp} className="text-xs text-status-danger font-mono">
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
			</CardContent>
			{footer !== "" ? (
				<CardFooter className="border-t border-border-subtle pt-2 text-xs text-text-secondary">
					{footer}
				</CardFooter>
			) : null}
		</CardPrimitive>
	);
}

export const Card: RefEntry = { factory, component: CardView };
