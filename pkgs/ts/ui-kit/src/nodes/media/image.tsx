// ImageRef -- display-only image by url with alt and fit mode.
//
// Server-owned. A write is a partial merge of {src, alt, fit, width, height,
// radius, aspect, zoom, download} into the node's props, which is the default store
// behaviour, so there is no handler. The fit and radius whitelists, the
// aspect spelling and the nullable-int coercion on width/height happen at
// read time. Composes the kit Image primitive; empty src renders the
// primitive's sunken placeholder.
//
// `radius` is the corner scale (none / sm / md / lg / full), none unless
// set. `aspect` holds
// the box to a ratio while the image loads and after ("16/9", "1:1", "4 / 3",
// or a bare number like 1.5); with it the image takes its container's width,
// since a ratio needs one side to come from somewhere.
//
// `zoom` draws the kit ImageViewer instead: wheel, pinch, drag, double click
// and keys to zoom and pan, a quiet control cluster on hover, a full window
// view. The viewer is a box the image moves inside, so it needs a size: the
// width, height and aspect props set it as above, and with no height and no
// aspect it is 320px tall and as wide as its container. `fit` does not apply,
// the viewer always opens fitted.
//
// `download`, a url, adds a download link: in the viewer's cluster, or as a
// chip over a plain image's corner, shown on hover and focus.

import type { CSSProperties } from "react";
import { Image } from "../../components/ui/image";
import { ImageViewer } from "../../components/ui/image-viewer";
import { MediaDownloadButton } from "../../components/ui/media-controls";
import { TooltipProvider } from "../../components/ui/tooltip";
import { cn } from "../../lib/utils";
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
	const radius = useEnumProp(path, "radius", RADII, "none");
	const aspect = normAspect(useStringProp(path, "aspect"));
	const zoom = useBoolProp(path, "zoom");
	const download = useStringProp(path, "download") || undefined;
	const style: CSSProperties = {};
	if (width != null) style.width = `${width}px`;
	if (height != null) style.height = `${height}px`;
	if (zoom) {
		return (
			<ImageViewer
				src={src || undefined}
				alt={alt}
				radius={radius}
				aspectRatio={height == null ? aspect : undefined}
				download={download}
				style={style}
			/>
		);
	}
	if (aspect != null && width == null) style.width = "100%";
	const image = (
		<Image
			src={src || undefined}
			alt={alt}
			fit={fit}
			radius={radius}
			aspectRatio={aspect}
			style={download ? { ...style, width: style.width && "100%" } : style}
		/>
	);
	if (!download || !src) return image;
	return (
		<TooltipProvider>
			<div
				data-slot="image-download"
				className="group/image relative w-fit max-w-full"
				style={{ width: style.width }}
			>
				{image}
				<MediaDownloadButton
					href={download}
					variant="secondary"
					tipSide="bottom"
					className={cn(
						"absolute top-2 right-2 shadow-raised",
						"opacity-0 transition-opacity duration-fast ease-out",
						"group-hover/image:opacity-100 focus-visible:opacity-100 [@media(hover:none)]:opacity-100",
					)}
				/>
			</div>
		</TooltipProvider>
	);
}

export const ImageRef: NodeEntry = { component: ImageView, fill: true };
