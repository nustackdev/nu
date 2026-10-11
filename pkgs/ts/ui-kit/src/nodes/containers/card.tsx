// Card -- card-styled Section. Header (title + subtitle), body (vertical
// stack of children), footer (plain text).
//
// Children are the node's own children in the tree, rendered by
// `NodeChildren`. Chrome still comes in over three dedicated ops rather than
// `write` -- `set_title`, `set_subtitle`, `set_footer`, each taking a string
// (nil coerces to "") -- and the store only knows `write` by default, so
// those three stay as handlers. Composes the kit Card primitive family.

import {
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	Card as CardPrimitive,
	CardTitle,
} from "../../components/ui/card";
import { NodeChildren, type NodeEntry, type NodeProps, useStringProp } from "../../tree";

function coerceStr(v: unknown): string {
	return v == null ? "" : String(v);
}

function CardView({ path }: NodeProps) {
	const title = useStringProp(path, "title");
	const subtitle = useStringProp(path, "subtitle");
	const footer = useStringProp(path, "footer");

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
				<NodeChildren path={path} />
			</CardContent>
			{footer !== "" ? (
				<CardFooter className="border-t border-border-subtle pt-2 text-xs text-text-secondary">
					{footer}
				</CardFooter>
			) : null}
		</CardPrimitive>
	);
}

export const Card: NodeEntry = {
	component: CardView,
	handlers: {
		set_title: (ctx, payload) =>
			ctx.update((props) => {
				props.title = coerceStr(payload);
			}),
		set_subtitle: (ctx, payload) =>
			ctx.update((props) => {
				props.subtitle = coerceStr(payload);
			}),
		set_footer: (ctx, payload) =>
			ctx.update((props) => {
				props.footer = coerceStr(payload);
			}),
	},
};
