// ButtonRef -- click trigger. Sends a notify on each click. No value.

import { OP_NOTIFY } from "../protocol";
import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

const factory: SliceFactory = (_path, _ctx) => ({
	type: "ButtonRef",
	value: null,
});

function ButtonView({ path }: { path: string }) {
	const send = useStore((s) => s.send);
	return (
		<button
			type="button"
			className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground hover:opacity-90"
			onClick={() => send({ op: OP_NOTIFY, ref: path, payload: null })}
		>
			{path}
		</button>
	);
}

export const ButtonRef: RefEntry = { factory, component: ButtonView };
