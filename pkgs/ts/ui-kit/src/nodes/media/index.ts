// Media node types: images, video, audio and files, server-owned and display only.

import type { NodeEntry } from "../../tree";
import { AudioRef } from "./audio";
import { FileRef } from "./file";
import { ImageRef } from "./image";
import { VideoRef } from "./video";

export const mediaEntries: Record<string, NodeEntry> = {
	ImageRef,
	VideoRef,
	AudioRef,
	FileRef,
};
