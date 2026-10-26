// Icons by name: any lucide glyph, named the way the wire names it.
//
// The wire carries lucide's own kebab name ("refresh-cw", "palette"), and
// every name lucide ships draws, its older names included ("home" is
// "house"). The names come from lucide's generated table, which maps each
// one to its own module, so a page bundles the table and fetches a glyph's
// drawing the first time something draws it. Nothing here lists icons.
//
// `iconFor` answers at once, so a node knows whether it has an icon before
// the drawing is in: an unknown name is null (warned once, so a typo shows
// in the console instead of a blank square), a known one a component that
// draws an empty svg of its own size until its drawing lands, then every
// copy of it from cache.

import { type IconNode, type LucideIcon, type LucideProps, Icon as LucideSvg } from "lucide-react";
import dynamicIconImports from "lucide-react/dynamicIconImports";
import { createElement, forwardRef, useEffect, useState } from "react";

type IconName = keyof typeof dynamicIconImports;

/** Every name lucide draws, its older names included. */
export const ICON_NAMES = Object.keys(dynamicIconImports) as readonly string[];

/** Whether `name` is one of lucide's. Quiet: an emoji or a typo is just false. */
export function isIconName(name: string): name is IconName {
	return Object.hasOwn(dynamicIconImports, name);
}

const drawn = new Map<string, IconNode>();
const loading = new Map<string, Promise<IconNode>>();
const glyphs = new Map<string, LucideIcon>();
const warned = new Set<string>();

function load(name: IconName): Promise<IconNode> {
	let pending = loading.get(name);
	if (!pending) {
		pending = dynamicIconImports[name]().then((mod) => {
			drawn.set(name, mod.__iconNode);
			return mod.__iconNode;
		});
		loading.set(name, pending);
	}
	return pending;
}

function glyph(name: IconName): LucideIcon {
	const Glyph = forwardRef<SVGSVGElement, Omit<LucideProps, "ref">>(
		({ className, ...props }, ref) => {
			const [node, setNode] = useState(() => drawn.get(name));
			useEffect(() => {
				if (node) return;
				let live = true;
				load(name).then(
					(got) => live && setNode(got),
					(error) => console.error(`[ui-kit] icon "${name}" did not load`, error),
				);
				return () => {
					live = false;
				};
			}, [node]);
			return createElement(LucideSvg, {
				ref,
				...props,
				className: className ? `lucide-${name} ${className}` : `lucide-${name}`,
				iconNode: node ?? [],
			});
		},
	);
	Glyph.displayName = `Icon(${name})`;
	return Glyph;
}

/** The icon for `name`, or null (warned once) when lucide has none of that name. */
export function iconFor(name: string): LucideIcon | null {
	if (name === "") return null;
	if (!isIconName(name)) {
		if (!warned.has(name)) {
			warned.add(name);
			console.warn(`[ui-kit] unknown icon "${name}"; drawing the label alone`);
		}
		return null;
	}
	let found = glyphs.get(name);
	if (!found) {
		found = glyph(name);
		glyphs.set(name, found);
	}
	return found;
}
