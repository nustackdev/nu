// Card -- card-styled Section. Media on top, header (title + subtitle, with
// actions on its right rail), body (vertical stack of children), footer.
//
// Children are the node's own children in the tree. Three segments are the
// card's named slots and draw in their place instead of in the body, the way
// a Tabs body is the child at its tab's id:
//   media   full-bleed on top (an image), above the header
//   actions the header's right rail, in a row flow so a Button, a Badge or
//           a Row of them sits at its own size (same key as a Section's)
//   footer  the bottom row (a button, a row of them); pinned to the card's
//           bottom edge, so in a grid row of stretched cards every footer
//           lines up whatever each body holds
// Every other child is the body, in write order. The string `caption` prop
// is a quiet line along the bottom, under a footer child when there is one.
//
// Chrome comes in over three dedicated ops rather than `write` --
// `set_title`, `set_subtitle`, `set_caption`, each taking a string (nil
// coerces to "") -- and the store only knows `write` by default, so those
// three are handlers. `variant`, `size`, `href` and `target` are plain props
// the default `write` merges. Composes the kit Card primitive family.
//
// Surface: `variant` is the look (default, elevated, sunken, outline, plain,
// accent, brand), `size` the preset for the whole look (pad 12 / 16 / 24 and
// the space between header, body and footer). The body speaks a stack's
// layers (`layout.tsx`): `padding` replaces the preset pad (the card's
// `--card-pad`), `gap` (3), `justify`, `align`, `divided`, the per child
// maps. The size props sit on the card; with `scroll` the body scrolls and
// the header and footer stay put.
//
// `href` makes the whole card one link: the primitive's `interactive` look
// (hover border, focus ring) `asChild` around a real <a>, so cmd-click and a
// host's AnchorCatcher both work. A link card should hold no controls
// of its own, since a button inside an anchor is two targets in one.

import type { CSSProperties } from "react";
import {
	CardAction,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	Card as CardPrimitive,
	CardTitle,
} from "../../components/ui/card";
import { anchorProps } from "../../lib/anchor";
import { cn } from "../../lib/utils";
import {
	ACTIONS_SLOT,
	type NodeEntry,
	type NodeProps,
	SlotView,
	useChildren,
	useEnumProp,
	useStringProp,
} from "../../tree";
import {
	childHandlers,
	flowClass,
	type LayoutDefaults,
	StackChildren,
	stepLength,
	useLayout,
} from "./layout";

const MEDIA = "media";
const FOOTER = "footer";
const SLOTS: ReadonlySet<string> = new Set([MEDIA, ACTIONS_SLOT, FOOTER]);

const VARIANTS = ["default", "elevated", "sunken", "outline", "plain", "accent", "brand"] as const;
const SIZES = ["sm", "md", "lg"] as const;
const DEFAULTS: LayoutDefaults = { gap: 3, justify: "start", align: "stretch" };

function coerceStr(v: unknown): string {
	return v == null ? "" : String(v);
}

function CardView({ path }: NodeProps) {
	const title = useStringProp(path, "title");
	const subtitle = useStringProp(path, "subtitle");
	const caption = useStringProp(path, "caption");
	const variant = useEnumProp(path, "variant", VARIANTS, "default");
	const size = useEnumProp(path, "size", SIZES, "md");
	const href = useStringProp(path, "href");
	const target = useStringProp(path, "target", "_self");
	const children = useChildren(path);
	const layout = useLayout(path, DEFAULTS);

	const hasMedia = children.includes(MEDIA);
	const hasActions = children.includes(ACTIONS_SLOT);
	const hasFooter = children.includes(FOOTER);
	const showHeader = title !== "" || subtitle !== "" || hasActions;
	const showFooter = caption !== "" || hasFooter;

	const inner = (
		<>
			{hasMedia ? (
				<div data-slot="card-media" className="[&_img]:w-full">
					<SlotView path={path} segment={MEDIA} />
				</div>
			) : null}
			{showHeader ? (
				<CardHeader>
					{title !== "" ? <CardTitle>{title}</CardTitle> : null}
					{subtitle !== "" ? <CardDescription>{subtitle}</CardDescription> : null}
					{hasActions ? (
						<CardAction>
							<SlotView path={path} segment={ACTIONS_SLOT} flow="row" />
						</CardAction>
					) : null}
				</CardHeader>
			) : null}
			<CardContent
				className={cn(
					"flex min-w-0 flex-col py-3",
					flowClass(layout, "column", { padding: false }),
					(showFooter || layout.scroll) && "flex-1",
				)}
				style={
					layout.divided
						? ({ "--flow-gap": stepLength(layout.gap ?? 3) } as CSSProperties)
						: undefined
				}
			>
				<StackChildren path={path} layout={layout} skip={SLOTS} />
			</CardContent>
			{hasFooter ? (
				<CardFooter className="mt-auto flex-col items-stretch">
					<SlotView path={path} segment={FOOTER} />
					{caption !== "" ? <p className="text-xs text-text-secondary">{caption}</p> : null}
				</CardFooter>
			) : caption !== "" ? (
				<CardFooter className="mt-auto border-t border-border-subtle pt-2 text-xs text-text-secondary">
					{caption}
				</CardFooter>
			) : null}
		</>
	);

	// Media bleeds to the card's edge, so the card clips it to its radius.
	const clip = hasMedia ? "overflow-hidden" : undefined;
	const style = {
		...layout.size,
		...(layout.padSet ? { "--card-pad": stepLength(layout.padding ?? 0) } : {}),
	} as CSSProperties;
	if (href === "") {
		return (
			<CardPrimitive variant={variant} size={size} className={clip} style={style}>
				{inner}
			</CardPrimitive>
		);
	}
	return (
		<CardPrimitive variant={variant} size={size} interactive asChild className={clip} style={style}>
			<a {...anchorProps(href, target)}>{inner}</a>
		</CardPrimitive>
	);
}

export const Card: NodeEntry = {
	component: CardView,
	fill: true,
	handlers: {
		set_title: (ctx, payload) =>
			ctx.update((props) => {
				props.title = coerceStr(payload);
			}),
		set_subtitle: (ctx, payload) =>
			ctx.update((props) => {
				props.subtitle = coerceStr(payload);
			}),
		set_caption: (ctx, payload) =>
			ctx.update((props) => {
				props.caption = coerceStr(payload);
			}),
		...childHandlers,
	},
};
