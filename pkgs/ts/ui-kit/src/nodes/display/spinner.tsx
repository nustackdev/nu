// SpinnerRef -- busy with no known progress. STUB: the smallest honest draw
// with the Spinner primitive; the display unit owns size and the setters.

import { Spinner } from "../../components/ui/spinner";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";

function SpinnerView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	return <Spinner label={label || undefined} />;
}

export const SpinnerRef: NodeEntry = { component: SpinnerView };
