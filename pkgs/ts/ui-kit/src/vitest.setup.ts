// Runs before every test file.
//
// Tests drive nodes with no server behind them, so nothing ever sends a
// `watch`. Count every event as watched, as a host with no watches would, so
// a test that dispatches a node event still sees its notify. A test about
// watching turns it off (`tree.getState().setWatchAll(false)`) and sends its
// own `watch` frames.

import { beforeEach } from "vitest";
import { tree } from "./tree/store";

beforeEach(() => {
	tree.getState().unwatchAll();
	tree.getState().setWatchAll(true);
});
