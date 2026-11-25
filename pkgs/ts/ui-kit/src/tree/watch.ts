// Which events the server listens for, per node.
//
// The server sends `watch {event}` on a ref when the first listener for that
// event binds and `unwatch` when the last one goes (`*` stands for every
// event). A node only sends an event someone watches, so a ref nobody
// listens to costs no frames.
//
// Stub: every event counts as watched until the watch table lands.

import type { Path } from "@nustackdev/ui-core";

/** The event a watch names to hear every event of a ref. */
export const ANY = "*";

/** Whether the server listens for `event` on the node at `path`. */
export function isWatched(_path: Path, _event: string): boolean {
	return true;
}
