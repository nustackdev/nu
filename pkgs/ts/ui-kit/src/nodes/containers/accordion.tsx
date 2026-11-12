// Accordion -- stack of collapsible sections, each wrapping one child node.
//
// Pairing: a section's body is the child whose segment is the section's id,
// whatever order the bodies were written in. Each body renders inside its
// own `AccordionContent`, so we place them with `NodeView` rather than
// `NodeChildren`. A section with no matching child renders empty; a child no
// section names is not drawn, and a notice under the sections names it.
//
// The tab owns `open` (toggle locally first, then notify); the server owns
// the section list. One `write` op multiplexes chrome updates by payload key:
//   {sections: [...]}  -> replace section list
//   {open:     [...]}  -> force open set
// That needs a handler because the default merge cannot do the multi=false
// clamp (several open ids collapse to the first). User toggles update local
// `open` then ship a `notify` whose payload is the post-toggle id list.
// Composes the kit Accordion primitive (Radix under the hood); the primitive
// owns chevron rotate + keyboard model. The size props and `scroll`
// (`layout.tsx`) sit on the accordion; each body is one child, which carries
// its own layers. Any other key of a write (a `set_layout`) merges as is.

import { OPS } from "@nustackdev/ui-core";
import {
	AccordionContent,
	AccordionItem,
	Accordion as AccordionPrimitive,
	AccordionTrigger,
} from "../../components/ui/accordion";
import {
	FlowProvider,
	type NodeEntry,
	type NodeProps,
	NodeView,
	useBoolProp,
	useChildren,
	useListProp,
	useSend,
	useSetProps,
} from "../../tree";
import { type LayoutDefaults, useLayout } from "./layout";
import { Unpaired } from "./unpaired";

type Section = { id: string; label: string };

const DEFAULTS: LayoutDefaults = {};

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

function AccordionView({ path }: NodeProps) {
	const rawSections = useListProp<unknown>(path, "sections");
	const rawOpen = useListProp<unknown>(path, "open");
	const multi = useBoolProp(path, "multi", true);
	const children = useChildren(path);
	const setProps = useSetProps(path);
	const send = useSend(path);
	const layout = useLayout(path, DEFAULTS);

	const sections = normalizeSections(rawSections);
	const bodies = new Set(children);
	const ids = new Set(sections.map((s) => s.id));
	const stray = children.filter((s) => !ids.has(s));
	const openRaw = normalizeOpen(rawOpen);
	// multi=false with multiple ids: keep the first, drop the rest.
	const open = !multi && openRaw.length > 1 ? [openRaw[0]] : openRaw;

	const notifyOpen = (next: string[]) => {
		setProps({ open: next });
		send(OPS.notify, next);
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
						<AccordionTrigger>{s.label}</AccordionTrigger>
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
