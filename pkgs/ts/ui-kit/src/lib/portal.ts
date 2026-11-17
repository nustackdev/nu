// Where floating content portals to.
//
// Menus, popovers and tooltips portal to document.body so no frame clips
// them. A full screen element is the one place that breaks: the browser shows
// only that element and what is inside it, so anything portalled to the body
// is drawn but never seen. A surface that goes full screen (a video frame)
// provides itself here while it is, and the floating content under it
// portals into it instead. Null, the default, is the body.

import { createContext, useContext } from "react";

export const PortalContainerContext = createContext<HTMLElement | null>(null);

/** The element floating content portals into: `own` when given, else the nearest provided one. */
export function usePortalContainer(own?: HTMLElement | null): HTMLElement | undefined {
	const near = useContext(PortalContainerContext);
	return own ?? near ?? undefined;
}
