// ImageRef -- display-only image by url with alt and fit mode.
//
// Server-owned. A write is a partial merge of {src, alt, fit, width, height,
// rounded} into the node's props, which is the default store behaviour, so
// there is no handler. The fit whitelist and the nullable-int coercion on
// width/height happen at read time now. Composes the kit Image primitive;
// empty src renders the primitive's sunken placeholder.

import type { CSSProperties } from "react";
import { Image } from "../../components/ui/image";
import { type NodeEntry, type NodeProps, useBoolProp, useProp, useStringProp } from "../../tree";

type Fit = "contain" | "cover" | "fill";

function normFit(v: string): Fit {
	if (v === "cover" || v === "contain" || v === "fill") return v;
	return "contain";
}

function asNullableInt(v: unknown): number | null {
	if (typeof v === "number") return v;
	return null;
}

function ImageView({ path }: NodeProps) {
	const src = useStringProp(path, "src");
	const alt = useStringProp(path, "alt");
	const fit = normFit(useStringProp(path, "fit", "contain"));
	const width = asNullableInt(useProp<unknown>(path, "width", null));
	const height = asNullableInt(useProp<unknown>(path, "height", null));
	const rounded = useBoolProp(path, "rounded");
	const style: CSSProperties = {};
	if (width != null) style.width = `${width}px`;
	if (height != null) style.height = `${height}px`;
	return (
		<Image
			src={src || undefined}
			alt={alt}
			fit={fit}
			radius={rounded ? "md" : "none"}
			style={style}
		/>
	);
}

export const ImageRef: NodeEntry = { component: ImageView };
