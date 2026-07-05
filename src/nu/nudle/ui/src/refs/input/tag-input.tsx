// TagInputRef -- multi-tag entry field. Browser is source of truth.
//
// Committed tags live on the slice as `value: string[]`; the half-typed
// `buffer` is browser-only and never serialized. Commit on Enter or comma;
// backspace with empty buffer drops the last tag. Every commit / remove
// fires one notify. Server write replaces the committed list wholesale;
// nil clears to []. Class-level defaults (label, placeholder, value,
// max_tags, allow_duplicates) seed the slice via mount props.

import type { KeyboardEvent } from "react";
import { OP_NOTIFY } from "../../protocol";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

function normalizeTags(raw: unknown): string[] {
	if (!Array.isArray(raw)) return [];
	const out: string[] = [];
	for (const item of raw) {
		if (typeof item === "string") out.push(item);
		else if (item != null) out.push(String(item));
	}
	return out;
}

const factory: SliceFactory = (path, ctx, props) => ({
	type: "TagInputRef",
	value: normalizeTags(props?.value),
	buffer: "",
	label: typeof props?.label === "string" ? (props.label as string) : "",
	placeholder: typeof props?.placeholder === "string" ? (props.placeholder as string) : "",
	maxTags: typeof props?.max_tags === "number" ? (props.max_tags as number) : null,
	allowDuplicates: props?.allow_duplicates === true,
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			if (v == null) {
				slice.value = [];
				return;
			}
			if (!Array.isArray(v)) return;
			slice.value = normalizeTags(v);
		}),
	get: () => {
		const slice = useStore.getState().refs[path];
		return (slice?.value as string[]) ?? [];
	},
});

function TagInputView({ path }: { path: string }) {
	const tags = useStore((s) => (s.refs[path]?.value as string[]) ?? []);
	const buffer = useStore((s) => (s.refs[path]?.buffer as string) ?? "");
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const placeholder = useStore((s) => (s.refs[path]?.placeholder as string) ?? "");
	const maxTags = useStore((s) => s.refs[path]?.maxTags as number | null | undefined);
	const allowDuplicates = useStore((s) => (s.refs[path]?.allowDuplicates as boolean) ?? false);
	const send = useStore((s) => s.send);

	const notify = () => send({ op: OP_NOTIFY, ref: path, payload: null });

	const setBuffer = (next: string) => {
		useStore.setState((draft) => {
			const slice = draft.refs[path];
			if (slice) slice.buffer = next;
		});
	};

	const commitBuffer = () => {
		const raw = (useStore.getState().refs[path]?.buffer as string) ?? "";
		const trimmed = raw.trim();
		if (trimmed === "") {
			if (raw !== "") setBuffer("");
			return;
		}
		const current = (useStore.getState().refs[path]?.value as string[]) ?? [];
		if (maxTags != null && current.length >= maxTags) {
			setBuffer("");
			return;
		}
		if (!allowDuplicates && current.includes(trimmed)) {
			setBuffer("");
			return;
		}
		useStore.setState((draft) => {
			const slice = draft.refs[path];
			if (!slice) return;
			slice.value = [...((slice.value as string[]) ?? []), trimmed];
			slice.buffer = "";
		});
		notify();
	};

	const removeAt = (idx: number) => {
		useStore.setState((draft) => {
			const slice = draft.refs[path];
			if (!slice) return;
			const next = ((slice.value as string[]) ?? []).slice();
			next.splice(idx, 1);
			slice.value = next;
		});
		notify();
	};

	const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
		if (e.key === "Enter") {
			e.preventDefault();
			commitBuffer();
			return;
		}
		if (e.key === ",") {
			e.preventDefault();
			commitBuffer();
			return;
		}
		if (e.key === "Backspace" && buffer === "" && tags.length > 0) {
			e.preventDefault();
			removeAt(tags.length - 1);
		}
	};

	return (
		<div className="flex flex-col gap-1 text-sm">
			{label && <span className="text-gray-700">{label}</span>}
			<div className="flex flex-wrap gap-1 rounded border px-2 py-1">
				{tags.map((t, i) => (
					<span
						key={`${i}:${t}`}
						className="flex items-center gap-1 rounded bg-gray-100 px-2 py-0.5 text-xs"
					>
						{t}
						<button
							type="button"
							className="text-gray-500 hover:text-gray-900"
							onClick={() => removeAt(i)}
						>
							x
						</button>
					</span>
				))}
				<input
					className="min-w-[6ch] flex-1 bg-transparent outline-none"
					value={buffer}
					placeholder={tags.length === 0 ? placeholder : ""}
					onChange={(e) => setBuffer(e.target.value)}
					onKeyDown={onKeyDown}
					onBlur={commitBuffer}
				/>
			</div>
		</div>
	);
}

export const TagInputRef: RefEntry = { factory, component: TagInputView };
