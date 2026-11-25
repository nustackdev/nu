// How a node tells the server something happened.
//
// Every notify names its event: `{event, ...fields}`. A node calls
// `emit(event, fields)` and nothing else; whether anyone listens (`watch.ts`)
// and when the frame goes out (`outbox.ts`) are not its business. An event
// nobody watches is dropped here, before it costs a frame.

import type { Path } from "@nustackdev/ui-core";
import { useCallback } from "react";
import { pathKey } from "./hooks";
import { enqueue } from "./outbox";
import { isWatched } from "./watch";

/** Extra payload fields an event carries next to its name (`value`, `values`, ...). */
export type EventFields = Record<string, unknown>;

/** Send `event` from one node. */
export type Emit = (event: string, fields?: EventFields) => void;

/** Emit `event` from the node at `path`, outside of render (handlers, effects, callbacks). */
export function emit(path: Path, event: string, fields?: EventFields): void {
	if (!isWatched(path, event)) return;
	enqueue(path, { ...fields, event }, event);
}

/** `emit` bound to one node, stable across renders. */
export function useEmit(path: Path): Emit {
	const key = pathKey(path);
	// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
	return useCallback((event: string, fields?: EventFields) => emit(path, event, fields), [key]);
}
