// The input contract, shared by every input node.
//
// Events. Every notify an input sends names its event: `{event: "change"}`
// when a value is committed, `{event: "submit", value}` when the person asks
// to send it (Enter in a single-line field, cmd/ctrl+Enter in a multi-line
// one), carrying the value sent, so `clear_on_submit` loses nothing. The
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
//
// Checks. A Form checks its inputs before it submits (`validateUnder`):
// required, min, max, max_length, pattern and the email / url formats. The
// browser's own bubble never shows (the form is `noValidate`); a failed check
// lands as the `check` prop on the control's Field (or on the control when it
// has none), the submit is dropped and the first failing control takes focus.
// A check clears as soon as its control is edited. The program's own errors
// (`set_errors`) land as `error` the same way and stay until the program
// clears them.
//
// Focus. A `focus` op stamps the node's `focus` prop with a fresh tick and
// the control focuses its element once per tick (`useFocusRequest`), so a
// request that lands before the node is drawn still focuses it on mount.
//
// Disabled. A Fieldset or a Form that is disabled disables every control
// under it (`DisabledScope`), on top of the control's own flag and its
// Field's.

import { type NodeHandler, OPS, type Path, type Props } from "@nustackdev/ui-core";
import type * as React from "react";
import {
	createContext,
	createElement,
	useCallback,
	useContext,
	useEffect,
	useId,
	useRef,
} from "react";
import { useFieldControl } from "../../components/ui/field";
import {
	type InputSpec,
	nodeAt,
	pathKey,
	resolve,
	tree,
	useBoolProp,
	useProp,
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
	const scoped = useContext(DisabledContext);
	const disabled = useBoolProp(path, "disabled") || Boolean(field?.disabled) || scoped;
	const readOnly = useBoolProp(path, "readonly");
	const required = useBoolProp(path, "required") || Boolean(field?.required);
	const autoFocus = useBoolProp(path, "autofocus");
	const size = inputSize(useStringProp(path, "size", "md"));
	const invalid = Boolean(field?.invalid);
	const id = field?.id ?? own;
	const describedBy = field?.describedBy;
	useControlId(path, id);
	useFocusRequest(path, id);
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
			clearCheck(path);
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
			clearCheck(path);
			send(OPS.notify, { event: EVENTS.change });
		},
		// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
		[key, setValue, send],
	);

	const submit = useCallback(
		(from?: Element | null) => {
			commit();
			// The submit carries what was sent, so a field that clears on submit
			// (or anything the program would otherwise read back) needs no read.
			send(OPS.notify, { event: EVENTS.submit, value: submitted(path) });
			requestFormSubmit(from ?? null);
			if (nodeAt(path)?.props.clear_on_submit) resetInput(path);
		},
		// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
		[key, commit, send],
	);

	return { edit, commit, pick, submit };
}

/** What a submit sends as `value`: the input's value as a form would gather it. */
export function submitted(path: Path): unknown {
	const node = nodeAt(path);
	const spec = specOf(node?.type ?? null);
	if (!node) return null;
	return spec?.read ? spec.read(node.props) : (node.props.value ?? null);
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
	clearCheck(path);
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
/** Text for an input whose empty is no value at all: "" and nil land as null. */
export const asTextOrNull = (raw: unknown): string | null =>
	raw == null || raw === "" ? null : String(raw);
export const asBool = (raw: unknown): boolean => Boolean(raw);

/** What a Form hands the controls inside it. */
export type FormState = { busy: boolean };

export const FormContext = createContext<FormState | null>(null);

/** The surrounding Form's state, or null outside one. */
export function useForm(): FormState | null {
	return useContext(FormContext);
}

// --- disabled cascade --------------------------------------------------------

const DisabledContext = createContext(false);

/** Disable every control under it, on top of a scope already around it. */
export function DisabledScope({
	disabled,
	children,
}: {
	disabled: boolean;
	children: React.ReactNode;
}): React.ReactElement {
	const outer = useContext(DisabledContext);
	return createElement(DisabledContext.Provider, { value: outer || disabled }, children);
}

/** Whether a disabled Fieldset or Form is around this node. */
export function useDisabledScope(): boolean {
	return useContext(DisabledContext);
}

// --- control ids --------------------------------------------------------------

/** The id of the element each drawn control puts its aria on, by path. */
const controlIds = new Map<string, string>();

function useControlId(path: Path, id: string): void {
	const key = pathKey(path);
	useEffect(() => {
		controlIds.set(key, id);
		return () => {
			if (controlIds.get(key) === id) controlIds.delete(key);
		};
	}, [key, id]);
}

/** The element a drawn control at `path` carries its id on, or null. */
export function controlElement(path: Path): HTMLElement | null {
	const id = controlIds.get(pathKey(path));
	return id ? document.getElementById(id) : null;
}

// --- focus --------------------------------------------------------------------

let focusTick = 0;
/** The last tick each path has focused for, so a remount does not focus again. */
const focusedAt = new Map<string, number>();

const FOCUSABLE =
	'input:not([type="hidden"]), textarea, select, button, [tabindex], [contenteditable="true"]';

function focusIn(el: HTMLElement | null): void {
	if (!el) return;
	const own = el.matches(FOCUSABLE) && el.tabIndex >= 0 ? el : null;
	const inner =
		own ??
		[...el.querySelectorAll<HTMLElement>(FOCUSABLE)].find(
			(x) => x.tabIndex >= 0 && !(x as HTMLInputElement).disabled,
		);
	inner?.focus();
}

/** Ask the control at `path` to take focus. Sends nothing. */
export function requestFocus(path: Path): void {
	if (!nodeAt(path)) return;
	focusTick += 1;
	tree.getState().setProps(path, { focus: focusTick });
}

/** The `focus` op every input answers. */
export const focusHandler = (ctx: { path: Path }) => requestFocus(ctx.path);

function useFocusRequest(path: Path, id: string): void {
	const tick = useProp<unknown>(path, "focus", 0);
	const key = pathKey(path);
	useEffect(() => {
		if (typeof tick !== "number" || tick <= (focusedAt.get(key) ?? 0)) return;
		focusedAt.set(key, tick);
		focusIn(document.getElementById(id));
	}, [key, tick, id]);
}

// --- checks and errors -----------------------------------------------------------

/** Where a control's error shows: the Field around it, or the control itself. */
export function errorTarget(path: Path): Path {
	const parent = path.slice(0, -1);
	const node = parent.length ? nodeAt(parent) : null;
	return node?.type && resolve(node.type)?.wraps ? parent : path;
}

/** Drop a failed check on the control at `path`: it was edited. */
export function clearCheck(path: Path): void {
	const at = errorTarget(path);
	if (nodeAt(at)?.props.check) tree.getState().setProps(at, { check: "" });
}

function isEmpty(v: unknown): boolean {
	return v == null || v === "" || v === false || (Array.isArray(v) && v.length === 0);
}

function bound(raw: unknown): number | string | null {
	if (typeof raw === "number" && Number.isFinite(raw)) return raw;
	if (typeof raw === "string" && raw !== "") return raw;
	return null;
}

/** What is wrong with one control's value, or "" when nothing is. */
export function checkControl(path: Path): string {
	const node = nodeAt(path);
	const spec = specOf(node?.type ?? null);
	if (!node || !spec) return "";
	const p = node.props;
	if (p.readonly) return "";
	const value = spec.read ? spec.read(p) : (p.value ?? null);
	// A Field marked required makes its control required, as it draws it.
	const at = errorTarget(path);
	const required = Boolean(p.required) || (at !== path && Boolean(nodeAt(at)?.props.required));
	if (isEmpty(value)) return required ? "This field is required" : "";
	const min = bound(p.min);
	const max = bound(p.max);
	if (typeof value === "number") {
		if (typeof min === "number" && value < min) return `Must be at least ${min}`;
		if (typeof max === "number" && value > max) return `Must be at most ${max}`;
	}
	if (typeof value === "string") {
		if (typeof min === "string" && value < min) return `Must be on or after ${min}`;
		if (typeof max === "string" && value > max) return `Must be on or before ${max}`;
		const limit = p.max_length;
		if (typeof limit === "number" && value.length > limit) {
			return `Must be at most ${limit} characters`;
		}
		if (typeof p.pattern === "string" && p.pattern !== "" && !matches(p.pattern, value)) {
			return "Does not match the expected format";
		}
		const el = controlElement(path);
		if (el instanceof HTMLInputElement && el.validity.typeMismatch) {
			return el.type === "email" ? "Enter an email address" : "Enter a valid value";
		}
	}
	return "";
}

function matches(pattern: string, value: string): boolean {
	try {
		return new RegExp(`^(?:${pattern})$`, "u").test(value);
	} catch {
		return true;
	}
}

function domOrder(a: Path, b: Path): number {
	const x = controlElement(a);
	const y = controlElement(b);
	if (!x || !y || x === y) return 0;
	return x.compareDocumentPosition(y) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
}

/**
 * Check every input under `path` and land each verdict as the `check` prop
 * on its Field (or itself): the message, or "" to clear. Hidden nodes and
 * anything under a disabled node are skipped, the way a browser skips a
 * disabled control. Returns the failing controls in page order.
 */
export function validateUnder(path: Path): Path[] {
	const bad: Path[] = [];
	const walk = (at: Path) => {
		const node = nodeAt(at);
		if (!node || node.hidden || node.props.disabled) return;
		const entry = node.type ? resolve(node.type) : undefined;
		if (entry?.input) {
			if (entry.input.gathered && !entry.input.gathered(node.props)) return;
			const message = checkControl(at);
			const target = errorTarget(at);
			if ((nodeAt(target)?.props.check ?? "") !== message) {
				tree.getState().setProps(target, { check: message });
			}
			if (message) bad.push(at);
			return;
		}
		for (const segment of node.children.keys()) walk([...at, segment]);
	};
	const root = nodeAt(path);
	if (root) for (const segment of root.children.keys()) walk([...path, segment]);
	return bad.sort(domOrder);
}

/**
 * Land the program's errors under `path`, keyed the way a submit's values
 * are (nested by segment, a Field standing for its control): each input's
 * Field (or the input) gets its message as `error`, every other one "".
 * Returns the first control named, in page order, or null.
 */
export function applyErrors(path: Path, errors: unknown): Path | null {
	const named: Path[] = [];
	const walk = (at: Path, errs: unknown) => {
		const node = nodeAt(at);
		if (!node) return;
		const entry = node.type ? resolve(node.type) : undefined;
		if (entry?.input || entry?.wraps) {
			// A Field stands for its one control: the error is the Field's, the
			// focus goes to the control.
			const first = node.children.keys().next();
			const control = entry.input ? at : first.done ? null : [...at, first.value];
			const message = typeof errs === "string" ? errs : "";
			if ((node.props.error ?? "") !== message) tree.getState().setProps(at, { error: message });
			if (message && control) named.push(control);
			return;
		}
		const inner = errs && typeof errs === "object" && !Array.isArray(errs) ? errs : {};
		for (const segment of node.children.keys()) {
			walk([...at, segment], (inner as Record<string, unknown>)[segment]);
		}
	};
	const root = nodeAt(path);
	const top = errors && typeof errors === "object" && !Array.isArray(errors) ? errors : {};
	if (root) {
		for (const segment of root.children.keys()) {
			walk([...path, segment], (top as Record<string, unknown>)[segment]);
		}
	}
	return named.sort(domOrder)[0] ?? null;
}
