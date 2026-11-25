// Where an event goes on its way to the server.
//
// Every emitted event lands here with its path, its payload and its name.
// The batching layer (queue the moving `input` events for a short window,
// flush everything at once when any other event comes in, one `batch` frame
// per flush) lives behind this one call, so no node knows about it.
//
// Stub: each event goes out as a notify right away.

import { OPS, type Path } from "@nustackdev/ui-core";
import { tree } from "./store";

/** Queue a notify from the node at `path`. `event` is the payload's own event name. */
export function enqueue(path: Path, payload: Record<string, unknown>, _event: string): void {
	tree.getState().send({ op: OPS.notify, ref: path, payload });
}
