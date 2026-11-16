// AudioRef -- display-only audio by url: one dense player row with a
// waveform to scrub.
//
// Server-owned. A write is a partial merge of {src, title, autoplay, loop}
// into the node's props, which is the default store behaviour, so there is
// no handler; playback stays in the browser and nothing is sent back.
// Composes the kit Audio primitive, which draws the waveform when the source
// allows a CORS fetch and a plain scrub bar when it does not.

import { Audio } from "../../components/ui/audio";
import { type NodeEntry, type NodeProps, useBoolProp, useStringProp } from "../../tree";

function AudioView({ path }: NodeProps) {
	const src = useStringProp(path, "src");
	const title = useStringProp(path, "title");
	const autoplay = useBoolProp(path, "autoplay");
	const loop = useBoolProp(path, "loop");
	return (
		<Audio src={src || undefined} title={title || undefined} autoPlay={autoplay} loop={loop} />
	);
}

export const AudioRef: NodeEntry = { component: AudioView, fill: true };
