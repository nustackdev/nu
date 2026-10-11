// ToggleRef -- two-state toolbar button. STUB: the smallest honest draw with
// the Toggle primitive, pressed state local to the tab; the inputs unit owns
// the read, the notify and the icon.

import { Toggle } from "../../components/ui/toggle";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useSetProps,
	useStringProp,
} from "../../tree";

function ToggleView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const pressed = useBoolProp(path, "pressed");
	const setProps = useSetProps(path);
	return (
		<Toggle pressed={pressed} onPressedChange={(next) => setProps({ pressed: next })}>
			{label}
		</Toggle>
	);
}

export const ToggleRef: NodeEntry = { component: ToggleView };
