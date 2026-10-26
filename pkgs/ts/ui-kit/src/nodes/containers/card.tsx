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
// It used to be called `footer`; that prop and its `set_footer` op are still
// read, so an older program's card keeps its caption.
//
// Chrome still comes in over three dedicated ops rather than `write` --
// `set_title`, `set_subtitle`, `set_caption`, each taking a string (nil
// coerces to "") -- and the store only knows `write` by default, so those
// three stay as handlers. `variant`, `size`, `href` and `target` are plain
// props the default `write` merges. Composes the kit Card primitive family.
//
// `href` makes the whole card one link: the primitive's `interactive` look
// (hover border, focus ring) `asChild` around a real <a>, so cmd-click and a
// host's AnchorCatcher both work. A link card should hold no controls
// of its own, since a button inside an anchor is two targets in one.

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
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	SlotView,
	useChildren,
	useEnumProp,
	useStringProp,
} from "../../tree";

const MEDIA = "media";
const FOOTER = "footer";
const SLOTS: ReadonlySet<string> = new Set([MEDIA, ACTIONS_SLOT, FOOTER]);

const VARIANTS = ["default", "elevated", "sunken", "outline"] as const;
const SIZES = ["sm", "md", "lg"] as const;

function coerceStr(v: unknown): string {
	return v == null ? "" : String(v);
}

function CardView({ path }: NodeProps) {
	const title = useStringProp(path, "title");
	const subtitle = useStringProp(path, "subtitle");
	const legacyCaption = useStringProp(path, "footer");
	const caption = useStringProp(path, "caption") || legacyCaption;
	const variant = useEnumProp(path, "variant", VARIANTS, "default");
	const size = useEnumProp(path, "size", SIZES, "md");
	const href = useStringProp(path, "href");
	const target = useStringProp(path, "target", "_self");
	const children = useChildren(path);

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
			<CardContent className={cn("flex flex-col gap-3 py-3", showFooter && "flex-1")}>
				<FlowProvider flow="block">
					<NodeChildren path={path} skip={SLOTS} />
				</FlowProvider>
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
	if (href === "") {
		return (
			<CardPrimitive variant={variant} size={size} className={clip}>
				{inner}
			</CardPrimitive>
		);
	}
	return (
		<CardPrimitive variant={variant} size={size} interactive asChild className={clip}>
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
		// The op's old name, from a program that predates `caption`.
		set_footer: (ctx, payload) =>
			ctx.update((props) => {
				props.caption = coerceStr(payload);
			}),
	},
};
