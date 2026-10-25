// ImageRef -- display-only image by url with alt and fit mode.
//
// Server-owned. A write is a partial merge of {src, alt, fit, width, height,
// rounded, radius, aspect} into the node's props, which is the default store
// behaviour, so there is no handler. The fit and radius whitelists, the
// aspect spelling and the nullable-int coercion on width/height happen at
// read time. Composes the kit Image primitive; empty src renders the
// primitive's sunken placeholder.
//
// `radius` is the corner scale (none / sm / md / lg / full). Empty means the
// older bool `rounded` decides: md when set, none when not. `aspect` holds
// the box to a ratio while the image loads and after ("16/9", "1:1", "4 / 3",
// or a bare number like 1.5); with it the image takes its container's width,
// since a ratio needs one side to come from somewhere.

import type { CSSProperties } from "react";
import { Image } from "../../components/ui/image";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useEnumProp,
	useProp,
	useStringProp,
} from "../../tree";

type Fit = "contain" | "cover" | "fill" | "none" | "scale-down";
type Radius = "none" | "sm" | "md" | "lg" | "full";

const FITS: readonly Fit[] = ["contain", "cover", "fill", "none", "scale-down"];
const RADII: readonly Radius[] = ["none", "sm", "md", "lg", "full"];

/** A CSS aspect-ratio from "16/9", "16:9", "16 / 9" or "1.5"; undefined when it reads as none. */
export function normAspect(v: string): string | undefined {
	const s = v.trim();
	if (s === "") return undefined;
	const m = /^(\d+(?:\.\d+)?)\s*[/:]\s*(\d+(?:\.\d+)?)$/.exec(s);
	if (m) return Number(m[2]) > 0 ? `${m[1]} / ${m[2]}` : undefined;
	const n = Number(s);
	return Number.isFinite(n) && n > 0 ? String(n) : undefined;
}

function asNullableInt(v: unknown): number | null {
	if (typeof v === "number") return v;
	return null;
}

function ImageView({ path }: NodeProps) {
	const src = useStringProp(path, "src");
	const alt = useStringProp(path, "alt");
	const fit = useEnumProp(path, "fit", FITS, "contain");
	const width = asNullableInt(useProp<unknown>(path, "width", null));
	const height = asNullableInt(useProp<unknown>(path, "height", null));
	const rounded = useBoolProp(path, "rounded");
	// An unset radius follows the older `rounded` flag.
	const radius = useEnumProp(path, "radius", RADII, rounded ? "md" : "none");
	const aspect = normAspect(useStringProp(path, "aspect"));
	const style: CSSProperties = {};
	if (width != null) style.width = `${width}px`;
	if (height != null) style.height = `${height}px`;
	if (aspect != null && width == null) style.width = "100%";
	return (
		<Image
			src={src || undefined}
			alt={alt}
			fit={fit}
			radius={radius}
			aspectRatio={aspect}
			style={style}
		/>
	);
}

export const ImageRef: NodeEntry = { component: ImageView, fill: true };
