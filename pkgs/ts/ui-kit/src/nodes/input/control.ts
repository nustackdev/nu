// The input contract, shared by every input node.
//
// Events. Every notify an input sends names its event: `{event: "change"}`
// when a value is committed, `{event: "submit"}` when the person asks to send
// it (Enter in a single-line field, cmd/ctrl+Enter in a multi-line one). The
// Python side filters on it: `on_change()` hears changes, `on_submit()` hears
// submits. A button sends `{event: "click"}`.
//
// Commits. A text-like input edits locally as you type (the store's `value`
// prop, so a read sees what is under the caret) and commits on blur and on
// submit. One commit path per node with a dirty check: a commit sends a
// change only when the value moved since the last one, so tabbing through a
// form sends nothing and Enter followed by blur sends one change, not two.
// Enter never blurs, and never fires while an IME is composing.
//
// Chrome. `useControl` folds the common props every input takes (label,
// disabled, readonly, required, autofocus, size, placeholder) with the
// surrounding kit Field, so the control gets the Field's id, describedby,
// invalid and required, and draws its own label only when the Field draws
// none.
//
// Forms. Enter inside a Form asks the form to submit (`requestSubmit`, with
// the form's first submit button as submitter, the way a browser's implicit
// submission picks it), so Enter in any single-line field submits whatever
// the field count. The Form node gathers the values (`gather`) and a reset
// puts every input back to its seed (`resetInput`).

import { type NodeHandler, OPS, type Path, type Props } from "@nustackdev/ui-core";
import type * as React from "react";
import { createContext, useCallback, useContext, useId, useRef } from "react";
import { useFieldControl } from "../../components/ui/field";
import {
	type InputSpec,
	nodeAt,
	pathKey,
	resolve,
	tree,
	useBoolProp,
	useSend,
	useSetValue,
	useStringProp,
} from "../../tree";

export const EVENTS = { change: "change", submit: "submit", click: "click" } as const;

/** Kit input sizes. A control's `xs` (a button step) draws as `sm`. */
export type InputSize = "sm" | "md" | "lg";

function inputSize(raw: string): InputSize {
	if (raw === "lg" || raw === "md" || raw === "sm") return raw;
	return raw === "xs" ? "sm" : "md";
}

export type Control = {
	/** The control's id: the Field's when inside one, else its own. */
	id: string;
	/** The label this node draws itself; empty inside a Field that labels it. */
	label: string;
	placeholder: string;
	disabled: boolean;
	readOnly: boolean;
	required: boolean;
	invalid: boolean;
	autoFocus: boolean;
	size: InputSize;
	describedBy: string | undefined;
	/** The surrounding Field's label id, for a group control that `<label for>` cannot name. */
	labelledBy: string | undefined;
	/** The attributes for the real element: spread them on the input. */
	aria: {
		id: string;
		"aria-describedby"?: string;
		"aria-invalid"?: boolean;
		"aria-required"?: boolean;
	};
};

/** The common props of every input, folded with the surrounding Field. */
export function useControl(path: Path): Control {
	const field = useFieldControl();
	const own = useId();
	const label = useStringProp(path, "label");
	const placeholder = useStringProp(path, "placeholder");
	const disabled = useBoolProp(path, "disabled") || Boolean(field?.disabled);
	const readOnly = useBoolProp(path, "readonly");
	const required = useBoolProp(path, "required") || Boolean(field?.required);
	const autoFocus = useBoolProp(path, "autofocus");
	const size = inputSize(useStringProp(path, "size", "md"));
	const invalid = Boolean(field?.invalid);
	const id = field?.id ?? own;
	const describedBy = field?.describedBy;
	return {
		id,
		label: field?.labelled ? "" : label,
		placeholder,
		disabled,
		readOnly,
		required,
		invalid,
		autoFocus,
		size,
		describedBy,
		labelledBy: field?.labelled ? field.labelId : undefined,
		aria: {
			id,
			"aria-describedby": describedBy,
			"aria-invalid": invalid || undefined,
			"aria-required": required || undefined,
		},
	};
}

function same(a: unknown, b: unknown): boolean {
	if (a === b) return true;
	if (Array.isArray(a) && Array.isArray(b)) {
		return a.length === b.length && a.every((x, i) => same(x, b[i]));
	}
	return false;
}

export type Commit = {
	/** A local edit: the value moves, nothing goes on the wire yet. */
	edit: (value: unknown) => void;
	/** Send a change if the value moved since the last one. */
	commit: () => void;
	/** Land a value and send its change now (a pick, a toggle, a stepper). */
	pick: (value: unknown) => void;
	/** Commit, send a submit, ask the enclosing Form to submit, then clear if asked. */
	submit: (from?: Element | null) => void;
};

/** One commit path per node, with the dirty check. */
export function useCommit(path: Path): Commit {
	const send = useSend(path);
	const setValue = useSetValue(path);
	const key = pathKey(path);
	// The value the server last heard about, once an edit started; null while clean.
	const base = useRef<{ value: unknown } | null>(null);

	const edit = useCallback(
		(value: unknown) => {
			if (base.current === null) base.current = { value: nodeAt(path)?.props.value };
			setValue(value);
		},
		// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
		[key, setValue],
	);

	const commit = useCallback(
		() => {
			const started = base.current;
			base.current = null;
			if (started === null) return;
			if (same(started.value, nodeAt(path)?.props.value)) return;
			send(OPS.notify, { event: EVENTS.change });
		},
		// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
		[key, send],
	);

	const pick = useCallback(
		(value: unknown) => {
			base.current = null;
			setValue(value);
			send(OPS.notify, { event: EVENTS.change });
		},
		[setValue, send],
	);

	const submit = useCallback(
		(from?: Element | null) => {
			commit();
			send(OPS.notify, { event: EVENTS.submit });
			requestFormSubmit(from ?? null);
			if (nodeAt(path)?.props.clear_on_submit) resetInput(path);
		},
		// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
		[key, commit, send],
	);

	return { edit, commit, pick, submit };
}

/** Enter that is not part of an IME composition. */
export function isEnter(e: React.KeyboardEvent): boolean {
	return e.key === "Enter" && !e.nativeEvent.isComposing && e.keyCode !== 229;
}

/** Ask the Form around `el` to submit, the way implicit submission would. */
export function requestFormSubmit(el: Element | null): void {
	const form = el?.closest("form");
	if (!form?.hasAttribute("data-nu-form")) return;
	const button = form.querySelector<HTMLButtonElement>('button[type="submit"]:not([disabled])');
	form.requestSubmit(button ?? undefined);
}

function specOf(type: string | null): InputSpec | undefined {
	return type ? resolve(type)?.input : undefined;
}

/** The value an input goes back to: its seed, or its type's empty value. */
export function seedValue(path: Path): unknown {
	const node = nodeAt(path);
	const spec = specOf(node?.type ?? null);
	if (!node || !spec) return undefined;
	if (node.seed && "value" in node.seed) return node.seed.value;
	return typeof spec.empty === "function" ? spec.empty(node.props) : spec.empty;
}

/** Put one input back to its seed. Sends nothing: the program asked, or a submit did. */
export function resetInput(path: Path): void {
	const node = nodeAt(path);
	if (!node || !specOf(node.type)) return;
	tree.getState().setProps(path, { value: seedValue(path) });
}

/** Put every input under `path` back to its seed. */
export function resetUnder(path: Path): void {
	const node = nodeAt(path);
	if (!node) return;
	if (specOf(node.type)) {
		resetInput(path);
		return;
	}
	for (const segment of node.children.keys()) resetUnder([...path, segment]);
}

/**
 * The values of every input under `path`, nested the way the tree is, keyed
 * by segment. A wrapper (a Field) stands for its one control, so a Field at
 * `title` gives `title: <its control's value>`. Hidden nodes and branches
 * with no input in them are left out.
 */
export function gather(path: Path): Props {
	const node = nodeAt(path);
	const out: Props = {};
	if (!node) return out;
	for (const [segment, child] of node.children) {
		if (child.hidden) continue;
		const found = inputValue([...path, segment]);
		if (found !== undefined) out[segment] = found.value;
	}
	return out;
}

function inputValue(path: Path): { value: unknown } | undefined {
	const node = nodeAt(path);
	if (!node || node.hidden) return undefined;
	const entry = node.type ? resolve(node.type) : undefined;
	const spec = entry?.input;
	if (spec) {
		if (spec.gathered && !spec.gathered(node.props)) return undefined;
		return { value: spec.read ? spec.read(node.props) : (node.props.value ?? null) };
	}
	if (entry?.wraps) {
		const first = node.children.keys().next();
		return first.done ? undefined : inputValue([...path, first.value]);
	}
	const nested = gather(path);
	return Object.keys(nested).length ? { value: nested } : undefined;
}

/** The `reset` op every input answers: back to its seed. */
export const resetHandler = (ctx: { path: Path }) => resetInput(ctx.path);

/**
 * The `write` op of an input. A map merges chrome (and `value`, if it names
 * one); anything else is the value. Either way the value goes through
 * `coerce`, so the control never sees a null or a stray type and never goes
 * uncontrolled.
 */
export function valueWrite(coerce: (raw: unknown, props: Props) => unknown): NodeHandler {
	return (ctx, payload) =>
		ctx.update((props) => {
			if (payload && typeof payload === "object" && !Array.isArray(payload)) {
				Object.assign(props, payload);
				if ("value" in payload) props.value = coerce(props.value, props);
				return;
			}
			props.value = coerce(payload, props);
		});
}

/** Coercions the inputs share. */
export const asText = (raw: unknown): string => (raw == null ? "" : String(raw));
export const asBool = (raw: unknown): boolean => Boolean(raw);

/** What a Form hands the controls inside it. */
export type FormState = { busy: boolean };

export const FormContext = createContext<FormState | null>(null);

/** The surrounding Form's state, or null outside one. */
export function useForm(): FormState | null {
	return useContext(FormContext);
}
