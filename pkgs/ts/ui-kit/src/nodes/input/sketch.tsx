// SketchRef -- a board a person draws on. Browser is source of truth.
//
// The value is the elements on `value` (paths, rects, ellipses, lines,
// arrows; see components/ui/sketch-board-model). The kit SketchBoard draws an
// element locally while the pointer moves and hands the new list over once it
// lands, and again on undo, redo and clear. Each is a local edit plus one
// notify, so a fast hand never floods the socket. A server-initiated read is
// answered by the store from `value`.
//
// In a Row it fills its share of the free width up to `width`, so a narrow
// screen gets a smaller board rather than a scrollbar. Config rides as props: `tools`, `controls`, `defaults`, `width`, `height`,
// `readonly`, `label`. The write handler is here because a list value needs
// care the default does not give: nil clears to [], a list replaces the
// elements wholesale (normalized against the board's defaults, so a program
// can leave out stroke and width), and a map merges config, with `value`
// normalized the same way. That is how a program, an agent or a replay draws.

import { OPS, type Props } from "@nustackdev/ui-core";
import { SketchBoard } from "../../components/ui/sketch-board";
import {
	normalizeElements,
	type SketchControl,
	type SketchDefaults,
	type SketchTool,
	sketchConfig,
} from "../../components/ui/sketch-board-model";
import { Text } from "../../components/ui/text";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useListProp,
	useNumberProp,
	useProp,
	useSend,
	useSetValue,
	useStringProp,
} from "../../tree";

function normalized(props: Props, raw: unknown) {
	return normalizeElements(raw, sketchConfig(props).defaults);
}

function SketchView({ path }: NodeProps) {
	const value = useListProp<unknown>(path, "value");
	const width = useNumberProp(path, "width", 280);
	const height = useNumberProp(path, "height", 0);
	const tools = useProp<SketchTool[] | null>(path, "tools", null);
	const controls = useProp<SketchControl[] | null>(path, "controls", null);
	const defaults = useProp<Partial<SketchDefaults> | null>(path, "defaults", null);
	const label = useStringProp(path, "label");
	const readonly = useBoolProp(path, "readonly");
	const setValue = useSetValue(path);
	const send = useSend(path);

	return (
		<div className="flex w-full min-w-0 flex-col gap-1" style={{ maxWidth: width }}>
			{label && (
				<Text as="span" size="sm" tone="secondary" weight="medium">
					{label}
				</Text>
			)}
			<SketchBoard
				value={value}
				width={width}
				height={height > 0 ? height : undefined}
				tools={tools ?? undefined}
				controls={controls ?? undefined}
				defaults={defaults ?? undefined}
				readonly={readonly}
				label={label || undefined}
				style={{ width: "100%", maxWidth: width }}
				onValueChange={(next) => {
					setValue(next);
					send(OPS.notify);
				}}
			/>
		</div>
	);
}

export const SketchRef: NodeEntry = {
	component: SketchView,
	// The board shrinks to its share of a row, keeping its aspect, and never
	// grows past its configured width.
	fill: true,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				if (payload == null) {
					props.value = [];
					return;
				}
				if (Array.isArray(payload)) {
					props.value = normalized(props, payload);
					return;
				}
				if (typeof payload === "object") {
					Object.assign(props, payload);
					if ("value" in payload) props.value = normalized(props, props.value);
				}
			}),
	},
};
