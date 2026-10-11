// Display node types: small status and identity marks, server-owned leaves.

import type { NodeEntry } from "../../tree";
import { AvatarRef } from "./avatar";
import { BreadcrumbRef } from "./breadcrumb";
import { SkeletonRef } from "./skeleton";
import { SpinnerRef } from "./spinner";
import { StatusPillRef } from "./status-pill";

export const displayEntries: Record<string, NodeEntry> = {
	AvatarRef,
	BreadcrumbRef,
	SkeletonRef,
	SpinnerRef,
	StatusPillRef,
};
