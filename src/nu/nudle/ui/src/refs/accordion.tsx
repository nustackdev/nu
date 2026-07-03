// AccordionRef -- stack of collapsible sections, each wrapping a child Ref.
//
// Tab owns `open` (toggle locally first, then notify); server owns the
// section list. One `write` op multiplexes chrome updates by payload key:
//   {sections: [...]}  -> replace section list
//   {open:     [...]}  -> force open set
// User toggles update local `open` then ship a `notify` whose payload is
// the post-toggle id list. Children are absolute wire paths from the
// mount field entry's nested `fields`, aligned by index to `sections`.

import { ErrorBoundary } from "@/components/ErrorBoundary";
import { OP_NOTIFY } from "../protocol";
import { renderers } from "../refs";
import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

type Section = { id: string; label: string };

function normalizeSections(raw: unknown): Section[] {
	if (!Array.isArray(raw)) return [];
	const out: Section[] = [];
	for (const item of raw) {
		if (item && typeof item === "object") {
			const o = item as { id?: unknown; label?: unknown };
			const id = o.id == null ? "" : String(o.id);
			const label = o.label == null ? "" : String(o.label);
			out.push({ id, label });
		}
	}
	return out;
}

function normalizeOpen(raw: unknown): string[] {
	if (!Array.isArray(raw)) return [];
	return raw.filter((x) => x != null).map((x) => String(x));
}

const factory: SliceFactory = (path, ctx, props, children) => {
	const initialSections = normalizeSections(props?.sections);
	const initialOpenRaw = normalizeOpen(props?.open);
	const initialMulti = props?.multi == null ? true : Boolean(props.multi);
	// multi=false with multiple ids: keep the first, drop the rest.
	const initialOpen =
		!initialMulti && initialOpenRaw.length > 1 ? [initialOpenRaw[0]] : initialOpenRaw;

	return {
		type: "AccordionRef",
		value: null,
		sections: initialSections,
		open: initialOpen,
		multi: initialMulti,
		children: Array.isArray(children) ? [...children] : [],
		write: (v) =>
			ctx.set((refs) => {
				const slice = refs[path];
				if (!slice) return;
				if (!v || typeof v !== "object" || Array.isArray(v)) return;
				const p = v as { sections?: unknown; open?: unknown; multi?: unknown };
				if ("sections" in p && p.sections != null) {
					slice.sections = normalizeSections(p.sections);
				}
				if ("open" in p && p.open != null) {
					const next = normalizeOpen(p.open);
					const multi = Boolean(slice.multi);
					slice.open = !multi && next.length > 1 ? [next[0]] : next;
				}
				if ("multi" in p && p.multi != null) {
					slice.multi = Boolean(p.multi);
				}
			}),
		notifyChanged: (next: string[]) => {
			ctx.set((refs) => {
				const slice = refs[path];
				if (slice) slice.open = [...next];
			});
			ctx.send({ op: OP_NOTIFY, ref: path, payload: next });
		},
	};
};

function AccordionView({ path }: { path: string }) {
	const sections = useStore((s) => (s.refs[path]?.sections as Section[]) ?? []);
	const open = useStore((s) => (s.refs[path]?.open as string[]) ?? []);
	const multi = useStore((s) => Boolean(s.refs[path]?.multi));
	const childPaths = useStore((s) => (s.refs[path]?.children as string[]) ?? []);
	const refs = useStore((s) => s.refs);
	const send = useStore((s) => s.send);

	const toggle = (id: string) => {
		const isOpen = open.includes(id);
		let next: string[];
		if (multi) {
			next = isOpen ? open.filter((x) => x !== id) : [...open, id];
		} else {
			next = isOpen ? [] : [id];
		}
		useStore.setState((draft) => {
			const slice = draft.refs[path];
			if (slice) slice.open = next;
		});
		send({ op: OP_NOTIFY, ref: path, payload: next });
	};

	return (
		<div className="flex flex-col border border-border rounded-md divide-y divide-border">
			{sections.map((s, i) => {
				const isOpen = open.includes(s.id);
				const cp = childPaths[i];
				return (
					<div key={`${i}-${s.id}`} className="flex flex-col">
						<button
							type="button"
							onClick={() => toggle(s.id)}
							className="flex items-center justify-between px-3 py-2 text-sm font-medium text-left hover:bg-muted"
							aria-expanded={isOpen}
						>
							<span>{s.label}</span>
							<span className="font-mono text-xs">{isOpen ? "-" : "+"}</span>
						</button>
						{isOpen ? (
							<div className="px-3 py-2">{cp ? <ChildSlot path={cp} refs={refs} /> : null}</div>
						) : null}
					</div>
				);
			})}
		</div>
	);
}

function ChildSlot({ path, refs }: { path: string; refs: Record<string, { type: string }> }) {
	const childSlice = refs[path];
	if (!childSlice) {
		return <div className="text-xs text-destructive font-mono">no ref at {path}</div>;
	}
	const Comp = renderers[childSlice.type];
	if (!Comp) {
		return (
			<div className="text-xs text-destructive font-mono">no renderer for {childSlice.type}</div>
		);
	}
	return (
		<ErrorBoundary label={`${path} (${childSlice.type})`}>
			<Comp path={path} />
		</ErrorBoundary>
	);
}

export const AccordionRef: RefEntry = { factory, component: AccordionView };
