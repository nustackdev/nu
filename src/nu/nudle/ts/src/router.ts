// Active-page routing for a mounted nudle payload.
//
// The Index carries a `pages` list keyed by route. If there is a NavRef in
// the structural fields, its current value picks the active route; otherwise
// we fall back to the first page. If the payload has no pages at all, the
// Index's own fields are the active surface.

import type { MountField, MountPayload } from "@nustackdev/ui-core";
import type { RefSlice } from "@nustackdev/ui-kit";

export function activeFields(
	page: MountPayload | null,
	refs: Record<string, RefSlice>,
): MountField[] | null {
	if (!page) return null;
	const pages = page.pages ?? [];
	if (pages.length === 0) return page.fields;
	const navField = page.fields.find((f) => f.type === "NavRef");
	const currentUri = navField ? (refs[navField.path]?.value as string | undefined) : undefined;
	const match = currentUri ? (pages.find((p) => p.route === currentUri) ?? pages[0]) : pages[0];
	return match.fields;
}
