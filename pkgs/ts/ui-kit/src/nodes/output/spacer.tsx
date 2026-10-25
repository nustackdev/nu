// SpacerRef -- empty room that takes what the line has left.
//
// No props. In a Row the cell grows from nothing (see Row), so the children
// after a spacer sit at the end of the line: a title on the left, actions on
// the right, with no `justify` on the row. In a Column it grows the same way
// down, pushing what follows to the bottom of a column that has a height of
// its own (a sidebar, a full height panel), and is nothing in one that sizes
// to its content. In a Grid it is an empty cell. In a Line there is no line
// to fill, so it draws nothing.
//
// `fill`, so a block flow draws it bare rather than in a content cell that
// would keep it at zero width, and `grow`, so a row's cell for it grows from
// nothing instead of from the fill basis.

import { type NodeEntry, useFlow } from "../../tree";

function SpacerView() {
	if (useFlow() === "inline") return null;
	return <div data-slot="spacer" aria-hidden="true" className="min-h-0 min-w-0 flex-1" />;
}

export const SpacerRef: NodeEntry = { component: SpacerView, fill: true, grow: true };
