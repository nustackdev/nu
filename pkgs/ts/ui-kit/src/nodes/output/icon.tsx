// IconRef -- one glyph by name, from the kit's curated lucide set.
//
// Server-owned, plain props merged by the default store `write`: `name` (a
// lucide name in kebab case, resolved through ./input/icons), `size` (xs, sm,
// md, lg, xl), `tone` (inherit, the text tiers, accent and the status hues),
// `framed` (set in a soft tinted square) and `label` (the accessible name;
// unset, the icon is decorative). Composes the kit Icon primitive. An
// unknown name draws nothing and warns once, as a button's icon does.
//
// In a Line (inline flow) it is a run of the sentence: text sized, on the
// baseline, in the text's color unless a tone says otherwise, so a check
// mark between two words reads as part of the line. Anywhere else it keeps
// its own size.

import { ICON_SIZES, ICON_TONES, Icon } from "../../components/ui/icon";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useEnumProp,
	useFlow,
	useStringProp,
} from "../../tree";
import { iconFor } from "../input/icons";

function IconView({ path }: NodeProps) {
	const name = useStringProp(path, "name");
	const size = useEnumProp(path, "size", ICON_SIZES, "md");
	const tone = useEnumProp(path, "tone", ICON_TONES, "inherit");
	const framed = useBoolProp(path, "framed");
	const label = useStringProp(path, "label");
	const inline = useFlow() === "inline";
	const glyph = iconFor(name);
	if (!glyph) return null;
	return (
		<Icon
			icon={glyph}
			size={size}
			tone={tone}
			inline={inline && !framed}
			framed={framed}
			label={label || undefined}
		/>
	);
}

export const IconRef: NodeEntry = { component: IconView };
