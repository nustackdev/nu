// ImageRef -- display-only image by url with alt and fit mode.
//
// Server-owned. One `write` op carries every mutation; payload is a partial
// map: missing keys leave the slice value untouched. Class-level defaults
// arrive on the mount field `props` and seed the slice.

import type { CSSProperties } from "react";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const FIT_CLASSES: Record<string, string> = {
	contain: "object-contain",
	cover: "object-cover",
	fill: "object-fill",
};

function asNullableInt(v: unknown): number | null {
	if (v == null) return null;
	if (typeof v === "number") return v;
	return null;
}

const factory: SliceFactory = (path, ctx, props) => ({
	type: "ImageRef",
	value: null,
	src: typeof props?.src === "string" ? (props.src as string) : "",
	alt: typeof props?.alt === "string" ? (props.alt as string) : "",
	fit: typeof props?.fit === "string" ? (props.fit as string) : "contain",
	width: asNullableInt(props?.width),
	height: asNullableInt(props?.height),
	rounded: typeof props?.rounded === "boolean" ? (props.rounded as boolean) : false,
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as {
				src?: unknown;
				alt?: unknown;
				fit?: unknown;
				width?: unknown;
				height?: unknown;
				rounded?: unknown;
			};
			if ("src" in p) slice.src = p.src == null ? "" : String(p.src);
			if ("alt" in p) slice.alt = p.alt == null ? "" : String(p.alt);
			if ("fit" in p) slice.fit = p.fit == null ? "contain" : String(p.fit);
			if ("width" in p) slice.width = asNullableInt(p.width);
			if ("height" in p) slice.height = asNullableInt(p.height);
			if ("rounded" in p) slice.rounded = p.rounded == null ? false : Boolean(p.rounded);
		}),
});

function ImageView({ path }: { path: string }) {
	const src = useStore((s) => (s.refs[path]?.src as string) ?? "");
	const alt = useStore((s) => (s.refs[path]?.alt as string) ?? "");
	const fit = useStore((s) => (s.refs[path]?.fit as string) ?? "contain");
	const width = useStore((s) => (s.refs[path]?.width as number | null | undefined) ?? null);
	const height = useStore((s) => (s.refs[path]?.height as number | null | undefined) ?? null);
	const rounded = useStore((s) => (s.refs[path]?.rounded as boolean) ?? false);
	const fitCls = FIT_CLASSES[fit] ?? FIT_CLASSES.contain;
	const roundedCls = rounded ? "rounded-md" : "";
	const style: CSSProperties = {};
	if (width != null) style.width = `${width}px`;
	if (height != null) style.height = `${height}px`;
	if (!src) {
		return <span className={`inline-block bg-gray-100 ${roundedCls}`} style={style} />;
	}
	return <img src={src} alt={alt} className={`${fitCls} ${roundedCls}`} style={style} />;
}

export const ImageRef: RefEntry = { factory, component: ImageView };
