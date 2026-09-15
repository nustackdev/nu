// Accordion -- stack of collapsible sections, each wrapping one child node.
//
// Pairing: the old module lined its `children` path list up with
// `sections[i]` by index. Tree children keep that rule -- `useChildren`
// gives the segments in insertion order (order of first write) and child `i`
// is the body of `sections[i]`, so the server still writes bodies in section
// order and nothing keys a body to a section id. Each body renders inside
// its own `AccordionContent`, so we place them with `NodeView` rather than
// `NodeChildren`. A section with no matching child renders empty, same as
// before.
//
// The tab owns `open` (toggle locally first, then notify); the server owns
// the section list. One `write` op multiplexes chrome updates by payload key:
//   {sections: [...]}  -> replace section list
//   {open:     [...]}  -> force open set
// That needs a handler because the default merge cannot do the multi=false
// clamp (several open ids collapse to the first). User toggles update local
// `open` then ship a `notify` whose payload is the post-toggle id list.
// Composes the kit Accordion primitive (Radix under the hood); the primitive
// owns chevron rotate + keyboard model.

import { OPS } from "@nustackdev/ui-core";
import {
	AccordionContent,
	AccordionItem,
	Accordion as AccordionPrimitive,
	AccordionTrigger,
} from "../../components/ui/accordion";
import {
	type NodeEntry,
	type NodeProps,
	NodeView,
	useBoolProp,
	useChildren,
	useListProp,
	useSend,
	useSetProps,
} from "../../tree";

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

function AccordionView({ path }: NodeProps) {
	const rawSections = useListProp<unknown>(path, "sections");
	const rawOpen = useListProp<unknown>(path, "open");
	const multi = useBoolProp(path, "multi", true);
	const children = useChildren(path);
	const setProps = useSetProps(path);
	const send = useSend(path);

	const sections = normalizeSections(rawSections);
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
		<AccordionPrimitive
			{...rootProps}
			className="rounded-md border border-border-default divide-y divide-border-subtle"
		>
			{sections.map((s, i) => {
				const segment = children[i];
				return (
					<AccordionItem key={`${i}-${s.id}`} value={s.id} className="px-3">
						<AccordionTrigger>{s.label}</AccordionTrigger>
						<AccordionContent>
							{segment ? <NodeView path={[...path, segment]} /> : null}
						</AccordionContent>
					</AccordionItem>
				);
			})}
		</AccordionPrimitive>
	);
}

export const Accordion: NodeEntry = {
	component: AccordionView,
	handlers: {
		write: (ctx, payload) => {
			if (!payload || typeof payload !== "object" || Array.isArray(payload)) return;
			const p = payload as { sections?: unknown; open?: unknown; multi?: unknown };
			ctx.update((props) => {
				if ("sections" in p && p.sections != null) {
					props.sections = normalizeSections(p.sections);
				}
				if ("open" in p && p.open != null) {
					// reads the pre-write `multi`, same order the old write used.
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
