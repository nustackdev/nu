// Grid -- children in equal cells. STUB: registered and drawing its children
// in the Grid primitive stub, so a program can use it today; the grid unit
// owns columns, gap, cell sizing and stories.
//
// Children see a "grid" flow: each one is a cell.

import { Grid as GridPrimitive } from "../../components/ui/grid";
import { FlowProvider, NodeChildren, type NodeEntry, type NodeProps } from "../../tree";

function GridView({ path }: NodeProps) {
	return (
		<GridPrimitive>
			<FlowProvider flow="grid">
				<NodeChildren path={path} />
			</FlowProvider>
		</GridPrimitive>
	);
}

export const Grid: NodeEntry = { component: GridView };
