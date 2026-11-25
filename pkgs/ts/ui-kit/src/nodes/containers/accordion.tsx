// Accordion -- stack of collapsible sections, each wrapping one child node.
//
// Pairing: a section's body is the child whose segment is the section's id,
// whatever order the bodies were written in. Each body renders inside its
// own `AccordionContent`, so we place them with `NodeView` rather than
// `NodeChildren`. A section with no matching child renders empty; a child no
// section names is not drawn, and a notice under the sections names it.
//
// A section's header: the child at `header:<id>`, when there is one, is its
// trigger row's content in place of `label` (see the primitive's `header`).
// A header key for a listed id is not a stray; one for an id no section has
// is named in the notice like a stray body.
//
// The tab owns `open` (toggle locally first, then emit); the server owns
// the section list. One `write` op multiplexes chrome updates by payload key:
//   {sections: [...]}  -> replace section list
//   {open:     [...]}  -> force open set
// That needs a handler because the default merge cannot do the multi=false
// clamp (several open ids collapse to the first). User toggles update local
// `open` then emit `change` whose `value` is the post-toggle id list, the
// same list a read answers (`readOpenIds`, clamped like the view).
// Composes the kit Accordion primitive (Radix under the hood); the primitive
// owns chevron rotate + keyboard model. The size props and `scroll`
// (`layout.tsx`) sit on the accordion; each body is one child, which carries
// its own layers. Any other key of a write (a `set_layout`) merges as is.

import {
	AccordionContent,
	AccordionItem,
	Accordion as AccordionPrimitive,
	AccordionTrigger,
} from "../../components/ui/accordion";
import {
	EVENTS,
	FlowProvider,
	type NodeEntry,
	type NodeProps,
	NodeView,
	SlotView,
	useBoolProp,
	useChildren,
	useEmit,
	useListProp,
	useSetProps,
} from "../../tree";
import { type LayoutDefaults, useLayout } from "./layout";
import { Unpaired } from "./unpaired";

type Section = { id: string; label: string };

const DEFAULTS: LayoutDefaults = {};

/** The child key of a section's header: this prefix plus the section id. */
const HEADER = "header:";

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

/** The open section ids as drawn: multi=false keeps only the first. */
function readOpenIds(props: Record<string, unknown>): string[] {
	const open = normalizeOpen(props.open);
	const multi = props.multi == null ? true : Boolean(props.multi);
	return !multi && open.length > 1 ? [open[0]] : open;
}

function AccordionView({ path }: NodeProps) {
	const rawSections = useListProp<unknown>(path, "sections");
	const rawOpen = useListProp<unknown>(path, "open");
	const multi = useBoolProp(path, "multi", true);
	const children = useChildren(path);
	const setProps = useSetProps(path);
	const emit = useEmit(path);
	const layout = useLayout(path, DEFAULTS);

	const sections = normalizeSections(rawSections);
	const bodies = new Set(children);
	const ids = new Set(sections.map((s) => s.id));
	const stray = children.filter((s) => !ids.has(s.startsWith(HEADER) ? s.slice(HEADER.length) : s));
	// multi=false with multiple ids: keep the first, drop the rest.
	const open = readOpenIds({ open: rawOpen, multi });

	const notifyOpen = (next: string[]) => {
		setProps({ open: next });
		emit(EVENTS.change, { value: next });
	};

	const rootProps = multi
		? {
				type: "multiple" as const,
				value: open,
				onValueChange: (next: string[]) => notifyOpen(next),
			}
		: {
				type: "single" as const,
				value: open[0] ?? "",
				collapsible: true,
				onValueChange: (next: string) => notifyOpen(next ? [next] : []),
			};

	return (
		<>
			<AccordionPrimitive
				{...rootProps}
				variant="boxed"
				className={layout.scroll}
				style={layout.size}
			>
				{sections.map((s, i) => (
					<AccordionItem key={`${i}-${s.id}`} value={s.id}>
						{bodies.has(HEADER + s.id) ? (
							<AccordionTrigger header={<SlotView path={path} segment={HEADER + s.id} />} />
						) : (
							<AccordionTrigger>{s.label}</AccordionTrigger>
						)}
						<AccordionContent>
							{bodies.has(s.id) ? (
								<FlowProvider flow="block">
									<NodeView path={[...path, s.id]} />
								</FlowProvider>
							) : null}
						</AccordionContent>
					</AccordionItem>
				))}
			</AccordionPrimitive>
			<Unpaired path={path} segments={stray} why="no section has that id" />
		</>
	);
}

export const Accordion: NodeEntry = {
	component: AccordionView,
	fill: true,
	reads: { "": readOpenIds },
	handlers: {
		write: (ctx, payload) => {
			if (!payload || typeof payload !== "object" || Array.isArray(payload)) return;
			const p = payload as { sections?: unknown; open?: unknown; multi?: unknown };
			const { sections: _s, open: _o, multi: _m, ...rest } = p as Record<string, unknown>;
			ctx.update((props) => {
				Object.assign(props, rest);
				if ("sections" in p && p.sections != null) {
					props.sections = normalizeSections(p.sections);
				}
				if ("open" in p && p.open != null) {
					// reads the pre-write `multi`: open is clamped before multi changes.
					const next = normalizeOpen(p.open);
					const multi = props.multi == null ? true : Boolean(props.multi);
					props.open = !multi && next.length > 1 ? [next[0]] : next;
				}
				if ("multi" in p && p.multi != null) {
					props.multi = Boolean(p.multi);
				}
			});
		},
	},
};
