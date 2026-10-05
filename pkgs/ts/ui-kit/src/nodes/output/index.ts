// Output node types: server-owned sinks rendered in the body.

import type { NodeEntry } from "../../tree";
import { AlertRef } from "./alert";
import { BadgeRef } from "./badge";
import { DividerRef } from "./divider";
import { EmptyStateRef } from "./empty-state";
import { GaugeRef } from "./gauge";
import { HeadingRef } from "./heading";
import { ImageRef } from "./image";
import { JsonViewerRef } from "./json-viewer";
import { KbdRef } from "./kbd";
import { LensRef } from "./lens";
import { LinkRef } from "./link";
import { ListRef } from "./list";
import { ProgressRef } from "./progress";
import { ShortcutRef } from "./shortcut";
import { StatRef } from "./stat";
import { StatusDotRef } from "./status-dot";
import { TableRef } from "./table";
import { TextRef } from "./text";
import { TreeRef } from "./tree";

export const outputEntries: Record<string, NodeEntry> = {
	HeadingRef,
	TextRef,
	ListRef,
	BadgeRef,
	StatusDotRef,
	KbdRef,
	ShortcutRef,
	AlertRef,
	StatRef,
	DividerRef,
	EmptyStateRef,
	ImageRef,
	LinkRef,
	ProgressRef,
	GaugeRef,
	TableRef,
	JsonViewerRef,
	LensRef,
	TreeRef,
};
