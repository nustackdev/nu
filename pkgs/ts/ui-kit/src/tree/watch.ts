// Which events the server listens for, per node.
//
// The server sends `watch {event}` on a ref when the first listener for that
// event binds and `unwatch` when the last one goes (`*` stands for every
// event). A node only sends an event someone watches, so a ref nobody
// listens to costs no frames.
//
// The table lives in the store (`@nustackdev/ui-core`), which takes the two
// ops off the wire like any other frame. It is keyed by path, not by node: a
// watch may land before the node is drawn, and it survives the node being
// removed and drawn again. A host clears it when it opens a new connection
// (`unwatchAll`), since the new session watches afresh.

import { ANY_EVENT, type Path } from "@nustackdev/ui-core";
import { tree } from "./store";

/** The event a watch names to hear every event of a ref. */
export const ANY = ANY_EVENT;

/** Whether the server listens for `event` on the node at `path`. */
export function isWatched(path: Path, event: string): boolean {
	return tree.getState().isWatched(path, event);
}
