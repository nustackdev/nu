// Flow: how a container lays out its children, handed down to them.
//
// The parent's flow decides how a child displays. The same Badge is a block
// in a Column, a cell in a Grid and a run of text in a Line, and the child
// never says which: every container provides its flow around its children,
// and a node that draws differently per flow reads it with `useFlow`.
//
//   block   stacked, one under the other (Column, Card, Form, ... and the
//           default when nothing provides one, e.g. at a page root)
//   row     side by side (Row)
//   grid    equal cells (Grid)
//   inline  wrapping like a paragraph (Line)
//
// `useFill` is the other half of a row's layout: a node type with no
// intrinsic width (a chart, a table, an input) registers `fill: true`, and
// the row gives it a share of the free width instead of its content size.

import type { Path } from "@nustackdev/ui-core";
import { createContext, type ReactNode, useContext } from "react";
import { useNode } from "./hooks";
import { isFill } from "./registry";

export type Flow = "block" | "row" | "grid" | "inline";

const FlowContext = createContext<Flow>("block");

/** Hand `flow` down to every node under `children`, until a container sets its own. */
export function FlowProvider({ flow, children }: { flow: Flow; children: ReactNode }) {
	return <FlowContext.Provider value={flow}>{children}</FlowContext.Provider>;
}

/** The flow of the nearest container above. "block" when there is none. */
export function useFlow(): Flow {
	return useContext(FlowContext);
}

/** Whether the node at `path` has no intrinsic width, read off its type's registry entry. */
export function useFill(path: Path): boolean {
	const { type, props } = useNode(path);
	return isFill(type, props);
}
