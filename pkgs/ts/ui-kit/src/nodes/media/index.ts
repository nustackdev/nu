// Media node types: images, video and audio, server-owned and display only.

import type { NodeEntry } from "../../tree";
import { AudioRef } from "./audio";
import { ImageRef } from "./image";
import { VideoRef } from "./video";

export const mediaEntries: Record<string, NodeEntry> = {
	ImageRef,
	VideoRef,
	AudioRef,
};
