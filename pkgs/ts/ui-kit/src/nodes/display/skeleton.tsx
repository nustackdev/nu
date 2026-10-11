// SkeletonRef -- a pulsing placeholder where content is still loading.
//
// Server-owned. A write is a partial merge of `lines` / `shape` / `height`
// into the node's props, which is the default store behaviour, so this type
// is a component and nothing else. Composes the kit Skeleton primitive:
// `text` stacks `lines` text bars with the last one shorter, the way a
// paragraph ends; `rect` is one block `height` px tall (96 when 0); `circle`
// is a disc `height` px across (40 when 0). Text and rect fill: they take
// the width they are given. A circle sizes to itself, so in a Row it keeps
// its disc instead of claiming a share of the free width.
// The shapes are aria-hidden; the region around them owns any live status.

import type { CSSProperties } from "react";
import { Skeleton } from "../../components/ui/skeleton";
import { type NodeEntry, type NodeProps, useNumberProp, useStringProp } from "../../tree";

type Shape = "text" | "rect" | "circle";

const SHAPES: Record<string, Shape> = { text: "text", rect: "rect", circle: "circle" };

const RECT_HEIGHT = 96;
const CIRCLE_SIZE = 40;
// Lines past this read as a wall, not a paragraph; a long body is a rect.
const MAX_LINES = 24;

function px(n: number, fallback: number): number {
	return n > 0 ? Math.floor(n) : fallback;
}

function SkeletonView({ path }: NodeProps) {
	const shape = SHAPES[useStringProp(path, "shape", "text")] ?? "text";
	const height = useNumberProp(path, "height", 0);
	const lines = Math.min(MAX_LINES, Math.max(1, Math.floor(useNumberProp(path, "lines", 1))));
	if (shape === "circle") {
		const size: CSSProperties = { width: px(height, CIRCLE_SIZE) };
		return (
			<div data-slot="skeleton-node" data-shape="circle">
				<Skeleton shape="circle" className="shrink-0" style={size} />
			</div>
		);
	}
	if (shape === "rect") {
		return (
			<div data-slot="skeleton-node" data-shape="rect" className="w-full">
				<Skeleton shape="rect" className="w-full" style={{ height: px(height, RECT_HEIGHT) }} />
			</div>
		);
	}
	return (
		<div data-slot="skeleton-node" data-shape="text" className="flex w-full flex-col gap-2">
			{Array.from({ length: lines }, (_, i) => (
				<Skeleton
					key={i}
					shape="text"
					className={lines > 1 && i === lines - 1 ? "w-3/5" : "w-full"}
				/>
			))}
		</div>
	);
}

export const SkeletonRef: NodeEntry = {
	component: SkeletonView,
	fill: (props) => props.shape !== "circle",
};
