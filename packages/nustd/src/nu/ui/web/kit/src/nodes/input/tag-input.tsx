// TagInputRef -- multi-tag entry field. Browser is source of truth.
//
// Committed tags live on the node as `value: string[]`. A pick or a removal is
// a local edit plus a notify. A server-initiated read is answered by the store
// from `value`.
//
// The write handler is here because a list value is not what the default write
// does: nil clears to [], a list replaces wholesale with every item stringified,
// and anything else is ignored outright rather than stomping the committed
// tags with a scalar. Chrome (label, placeholder, max_tags, allow_duplicates)
// is just more props. Composes the kit TagInput primitive; the primitive owns
// the buffer + commit-on-Enter/comma + remove-on-Backspace behavior.

import { OPS } from "@nustackdev/ui-core";
import { useId } from "react";
import { TagInput } from "../../components/ui/tag-input";
import {
	type NodeEntry,
	type NodeProps,
	useListProp,
	useProp,
	useSend,
	useSetValue,
	useStringProp,
} from "../../tree";

function normalizeTags(raw: unknown): string[] {
	if (!Array.isArray(raw)) return [];
	const out: string[] = [];
	for (const item of raw) {
		if (typeof item === "string") out.push(item);
		else if (item != null) out.push(String(item));
	}
	return out;
}

function TagInputView({ path }: NodeProps) {
	const tags = useListProp<string>(path, "value");
	const label = useStringProp(path, "label");
	const placeholder = useStringProp(path, "placeholder");
	const rawMax = useProp<unknown>(path, "max_tags", null);
	const maxTags = typeof rawMax === "number" ? rawMax : null;
	const setValue = useSetValue(path);
	const send = useSend(path);
	const id = useId();

	return (
		<div className="flex flex-col gap-1">
			{label && (
				<label htmlFor={id} className="text-sm font-medium text-text-secondary">
					{label}
				</label>
			)}
			<TagInput
				id={id}
				value={tags}
				maxTags={maxTags ?? undefined}
				placeholder={placeholder || undefined}
				onValueChange={(next) => {
					setValue(next);
					send(OPS.notify);
				}}
			/>
		</div>
	);
}

export const TagInputRef: NodeEntry = {
	component: TagInputView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				if (payload == null) {
					props.value = [];
					return;
				}
				if (!Array.isArray(payload)) return;
				props.value = normalizeTags(payload);
			}),
	},
};
