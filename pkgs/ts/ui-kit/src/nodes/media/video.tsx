// VideoRef -- display-only video by url, played with the kit transport.
//
// Server-owned. A write is a partial merge of {src, poster, fit, width,
// height, radius, aspect, autoplay, loop, muted, download} into the node's props, which
// is the default store behaviour, so there is no handler; playback stays in
// the browser and nothing is sent back. Whitelists and the nullable-int
// coercion happen at read time, like ImageRef. Composes the kit Video
// primitive; empty src draws its "No video" frame.
//
// `aspect` holds the frame to a ratio ("16/9", "1:1", "4 / 3", 1.5); without
// one the frame takes the video's own shape once it loads. `radius` is the
// corner scale (none / sm / md / lg), none unless set. Autoplay only starts
// muted in most browsers. `download`, a url, puts a download link in the
// transport.

import type { CSSProperties } from "react";
import { Video } from "../../components/ui/video";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useEnumProp,
	useProp,
	useStringProp,
} from "../../tree";
import { normAspect } from "./image";

type Fit = "contain" | "cover" | "fill";
type Radius = "none" | "sm" | "md" | "lg";

const FITS: readonly Fit[] = ["contain", "cover", "fill"];
const RADII: readonly Radius[] = ["none", "sm", "md", "lg"];

function asNullableInt(v: unknown): number | null {
	return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function VideoView({ path }: NodeProps) {
	const src = useStringProp(path, "src");
	const poster = useStringProp(path, "poster");
	const fit = useEnumProp(path, "fit", FITS, "contain");
	const width = asNullableInt(useProp<unknown>(path, "width", null));
	const height = asNullableInt(useProp<unknown>(path, "height", null));
	const radius = useEnumProp(path, "radius", RADII, "none");
	const aspect = normAspect(useStringProp(path, "aspect"));
	const autoplay = useBoolProp(path, "autoplay");
	const loop = useBoolProp(path, "loop");
	const muted = useBoolProp(path, "muted");
	const download = useStringProp(path, "download");
	const style: CSSProperties = {};
	if (width != null) style.width = `${width}px`;
	if (height != null) style.height = `${height}px`;
	return (
		<Video
			src={src || undefined}
			poster={poster || undefined}
			fit={fit}
			radius={radius}
			aspectRatio={aspect}
			autoPlay={autoplay}
			loop={loop}
			muted={muted}
			download={download || undefined}
			style={style}
		/>
	);
}

export const VideoRef: NodeEntry = { component: VideoView, fill: true };
