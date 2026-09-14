// Output node types: server-owned sinks rendered in the body.

import type { NodeEntry } from "../../tree";
import { AlertRef } from "./alert";
import { BadgeRef } from "./badge";
import { CodeBlockRef } from "./code-block";
import { DividerRef } from "./divider";
import { GaugeRef } from "./gauge";
import { HeadingRef } from "./heading";
import { ImageRef } from "./image";
import { JsonViewerRef } from "./json-viewer";
import { LinkRef } from "./link";
import { MarkdownRef } from "./markdown";
import { ProgressRef } from "./progress";
import { StatRef } from "./stat";
import { TableRef } from "./table";
import { TextRef } from "./text";

export const outputEntries: Record<string, NodeEntry> = {
	HeadingRef,
	TextRef,
	MarkdownRef,
	BadgeRef,
	AlertRef,
	StatRef,
	DividerRef,
	CodeBlockRef,
	ImageRef,
	LinkRef,
	ProgressRef,
	GaugeRef,
	TableRef,
	JsonViewerRef,
};
