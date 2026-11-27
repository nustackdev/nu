// MenuSheet: a menu as a bottom sheet, the touch presentation of the kit's
// DropdownMenu and ContextMenu.
// Design refs:
//   language/mobile.md  overlays become bottom sheets, rows at 44px
//   primitives.md       §DropdownMenu (the parts this mirrors one to one)
//
// Not exported from the kit. DropdownMenu and ContextMenu read `useTouch()`
// in every part and render the matching part from here, so callers keep one
// API. The parts mirror Radix's menu semantics where callers rely on them:
// `onSelect` fires on a tap and closes the menu unless the handler calls
// `preventDefault()`, checkbox and radio items report through
// `onCheckedChange` / `onValueChange`, and a submenu holds its own open state.
//
// The sheet is a dialog of buttons, not a `role=menu`: there is no roving
// focus on a phone, and a checkbox or radio row says what it is with its own
// role. A submenu expands in place under its row rather than stacking a
// second sheet: one surface under the thumb, the way back is the same row.

import { Check, ChevronRight, Circle } from "lucide-react";
import { Slot as SlotPrimitive } from "radix-ui";
import * as React from "react";

import { cn } from "../../lib/utils";
import {
	BottomSheet,
	BottomSheetContent,
	type BottomSheetContentProps,
	bottomSheetItemVariants,
} from "./bottom-sheet";

// A tiny controllable state: the caller's `open` wins when given, ours
// otherwise, and every change is reported.
function useControllable(
	value: boolean | undefined,
	initial: boolean | undefined,
	onChange: ((next: boolean) => void) | undefined,
): [boolean, (next: boolean) => void] {
	const [inner, setInner] = React.useState(initial ?? false);
	const current = value ?? inner;
	const set = React.useCallback(
		(next: boolean) => {
			if (value === undefined) setInner(next);
			onChange?.(next);
		},
		[value, onChange],
	);
	return [current, set];
}

interface MenuSheetState {
	open: boolean;
	setOpen: (open: boolean) => void;
}

const MenuSheetContext = React.createContext<MenuSheetState | null>(null);

/** The open state of the enclosing menu sheet. Throws outside one. */
function useMenuSheet(): MenuSheetState {
	const ctx = React.useContext(MenuSheetContext);
	if (!ctx) throw new Error("MenuSheet parts must sit inside a DropdownMenu or ContextMenu");
	return ctx;
}

interface MenuSheetProps {
	open?: boolean;
	defaultOpen?: boolean;
	onOpenChange?: (open: boolean) => void;
	children?: React.ReactNode;
}

function MenuSheet({ open, defaultOpen, onOpenChange, children }: MenuSheetProps) {
	const [current, setOpen] = useControllable(open, defaultOpen, onOpenChange);
	const state = React.useMemo(() => ({ open: current, setOpen }), [current, setOpen]);
	return (
		<MenuSheetContext.Provider value={state}>
			<BottomSheet open={current} onOpenChange={setOpen}>
				{children}
			</BottomSheet>
		</MenuSheetContext.Provider>
	);
}

// What a Radix menu content takes that a dialog does not: placement, and the
// keyboard loop. Dropped here so they never reach the sheet's DOM.
type MenuOnlyProps =
	| "side"
	| "sideOffset"
	| "align"
	| "alignOffset"
	| "avoidCollisions"
	| "collisionBoundary"
	| "collisionPadding"
	| "arrowPadding"
	| "sticky"
	| "hideWhenDetached"
	| "updatePositionStrategy"
	| "loop"
	| "forceMount";

/** Strip the menu-only props off a Radix menu content's props. */
function sheetContentProps<T extends Record<string, unknown>>(props: T): Omit<T, MenuOnlyProps> {
	const {
		side: _side,
		sideOffset: _sideOffset,
		align: _align,
		alignOffset: _alignOffset,
		avoidCollisions: _avoidCollisions,
		collisionBoundary: _collisionBoundary,
		collisionPadding: _collisionPadding,
		arrowPadding: _arrowPadding,
		sticky: _sticky,
		hideWhenDetached: _hideWhenDetached,
		updatePositionStrategy: _updatePositionStrategy,
		loop: _loop,
		forceMount: _forceMount,
		...rest
	} = props;
	return rest;
}

type MenuSheetContentProps = Omit<BottomSheetContentProps, "title" | "label" | "bodyClassName">;

// The caller's classes style the body, as on Popover: a width or a min width
// set for the anchored menu yields to the sheet's.
function MenuSheetContent({ className, children, ...props }: MenuSheetContentProps) {
	return (
		<BottomSheetContent
			label={props["aria-label"] ?? "Menu"}
			bodyClassName={cn(className, "w-full min-w-0 max-w-none")}
			{...props}
		>
			{children}
		</BottomSheetContent>
	);
}

// Radix's select event: cancelable, so a handler that calls preventDefault()
// keeps the menu open (a toggle the user flips twice, a rename in place).
function runSelect(onSelect: ((event: Event) => void) | undefined, close: () => void) {
	const event = new Event("menu.itemselect", { cancelable: true });
	onSelect?.(event);
	if (!event.defaultPrevented) close();
}

interface MenuSheetItemProps extends Omit<React.HTMLAttributes<HTMLElement>, "onSelect"> {
	onSelect?: (event: Event) => void;
	disabled?: boolean;
	variant?: "default" | "danger";
	inset?: boolean;
	asChild?: boolean;
	/** Radix's typeahead text. Nothing to type ahead on a sheet. */
	textValue?: string;
	/** A leading lane, for rows that line up under checkbox and radio rows. */
	lane?: React.ReactNode;
	role?: string;
}

function MenuSheetItem({
	className,
	onSelect,
	onClick,
	disabled,
	variant = "default",
	inset,
	asChild,
	textValue: _textValue,
	lane,
	children,
	...props
}: MenuSheetItemProps) {
	const { setOpen } = useMenuSheet();
	const Comp = asChild ? SlotPrimitive.Slot : "button";
	return (
		<Comp
			type={asChild ? undefined : "button"}
			data-slot="menu-sheet-item"
			data-variant={variant}
			data-disabled={disabled || undefined}
			aria-disabled={asChild && disabled ? true : undefined}
			disabled={asChild ? undefined : disabled}
			className={cn(
				bottomSheetItemVariants({ variant }),
				"data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
				inset && "pl-8",
				className,
			)}
			onClick={(e: React.MouseEvent<HTMLElement>) => {
				onClick?.(e);
				if (e.defaultPrevented || disabled) return;
				runSelect(onSelect, () => setOpen(false));
			}}
			{...props}
		>
			{asChild ? (
				children
			) : (
				<>
					{lane}
					{children}
				</>
			)}
		</Comp>
	);
}

// The check and the radio dot carry `!`: the row's own `[&_svg]` size and tint
// would otherwise win. The lane is there checked or not, so labels line up.
function Lane({ children }: { children?: React.ReactNode }) {
	return <span className="flex size-4 shrink-0 items-center justify-center">{children}</span>;
}

interface MenuSheetCheckboxItemProps extends MenuSheetItemProps {
	checked?: boolean | "indeterminate";
	onCheckedChange?: (checked: boolean) => void;
}

function MenuSheetCheckboxItem({
	checked = false,
	onCheckedChange,
	onSelect,
	inset: _inset,
	...props
}: MenuSheetCheckboxItemProps) {
	return (
		<MenuSheetItem
			role="checkbox"
			aria-checked={checked === "indeterminate" ? "mixed" : checked}
			data-state={
				checked === true ? "checked" : checked === "indeterminate" ? "indeterminate" : "unchecked"
			}
			lane={<Lane>{checked === true && <Check className="size-3.5! text-accent-text!" />}</Lane>}
			onSelect={(e) => {
				onCheckedChange?.(checked === "indeterminate" ? true : !checked);
				onSelect?.(e);
			}}
			{...props}
		/>
	);
}

interface RadioState {
	value?: string;
	onValueChange?: (value: string) => void;
}

const RadioContext = React.createContext<RadioState>({});

interface MenuSheetRadioGroupProps extends React.HTMLAttributes<HTMLDivElement> {
	value?: string;
	onValueChange?: (value: string) => void;
}

function MenuSheetRadioGroup({
	value,
	onValueChange,
	asChild: _asChild,
	...props
}: MenuSheetRadioGroupProps & { asChild?: boolean }) {
	const state = React.useMemo(() => ({ value, onValueChange }), [value, onValueChange]);
	return (
		<RadioContext.Provider value={state}>
			<div role="radiogroup" data-slot="menu-sheet-radio-group" {...props} />
		</RadioContext.Provider>
	);
}

interface MenuSheetRadioItemProps extends MenuSheetItemProps {
	value: string;
}

function MenuSheetRadioItem({ value, onSelect, inset: _inset, ...props }: MenuSheetRadioItemProps) {
	const group = React.useContext(RadioContext);
	const checked = group.value === value;
	return (
		<MenuSheetItem
			role="radio"
			aria-checked={checked}
			data-state={checked ? "checked" : "unchecked"}
			lane={
				<Lane>{checked && <Circle className="size-2! fill-accent-text text-accent-text!" />}</Lane>
			}
			onSelect={(e) => {
				group.onValueChange?.(value);
				onSelect?.(e);
			}}
			{...props}
		/>
	);
}

interface MenuSheetLabelProps extends React.HTMLAttributes<HTMLDivElement> {
	inset?: boolean;
	asChild?: boolean;
}

function MenuSheetLabel({ className, inset, asChild, ...props }: MenuSheetLabelProps) {
	const Comp = asChild ? SlotPrimitive.Slot : "div";
	return (
		<Comp
			data-slot="menu-sheet-label"
			className={cn(
				"px-1 pt-3 pb-1 text-xs font-medium text-text-secondary",
				inset && "pl-8",
				className,
			)}
			{...props}
		/>
	);
}

// Rows already draw a hairline between them, so a group break is a stronger
// line laid over the last row's hairline, then air before the next group.
function MenuSheetSeparator({
	className,
	asChild: _asChild,
	...props
}: React.HTMLAttributes<HTMLHRElement> & { asChild?: boolean }) {
	return (
		<hr
			data-slot="menu-sheet-separator"
			className={cn("relative -mt-px mb-2 border-t border-border-default", className)}
			{...props}
		/>
	);
}

function MenuSheetGroup({
	asChild: _asChild,
	...props
}: React.HTMLAttributes<HTMLDivElement> & { asChild?: boolean }) {
	// A fieldset would bring its own border and padding; a group role is all we need.
	// biome-ignore lint/a11y/useSemanticElements: see above.
	return <div role="group" data-slot="menu-sheet-group" {...props} />;
}

interface SubState {
	open: boolean;
	setOpen: (open: boolean) => void;
	id: string;
}

const SubContext = React.createContext<SubState | null>(null);

function MenuSheetSub({ open, defaultOpen, onOpenChange, children }: MenuSheetProps) {
	const [current, setOpen] = useControllable(open, defaultOpen, onOpenChange);
	const id = React.useId();
	const state = React.useMemo(() => ({ open: current, setOpen, id }), [current, setOpen, id]);
	return <SubContext.Provider value={state}>{children}</SubContext.Provider>;
}

function MenuSheetSubTrigger({ children, onSelect: _onSelect, ...props }: MenuSheetItemProps) {
	const sub = React.useContext(SubContext);
	const open = sub?.open ?? false;
	return (
		<MenuSheetItem
			aria-expanded={open}
			aria-controls={sub?.id}
			data-state={open ? "open" : "closed"}
			onSelect={(e) => {
				// A submenu row opens its rows, it never closes the sheet.
				e.preventDefault();
				sub?.setOpen(!open);
			}}
			{...props}
		>
			{children}
			<ChevronRight
				className={cn("ml-auto transition-transform duration-fast ease-out", open && "rotate-90")}
			/>
		</MenuSheetItem>
	);
}

// The submenu's rows, in place under its row and stepped in one lane. A
// submenu's dismiss handlers mean nothing inline; placement is stripped by
// the caller with `sheetContentProps`.
function MenuSheetSubContent({
	className,
	onEscapeKeyDown: _onEscapeKeyDown,
	onFocusOutside: _onFocusOutside,
	onInteractOutside: _onInteractOutside,
	onPointerDownOutside: _onPointerDownOutside,
	...props
}: React.HTMLAttributes<HTMLDivElement> & {
	onEscapeKeyDown?: unknown;
	onFocusOutside?: unknown;
	onInteractOutside?: unknown;
	onPointerDownOutside?: unknown;
}) {
	const sub = React.useContext(SubContext);
	if (!sub?.open) return null;
	return (
		// biome-ignore lint/a11y/useSemanticElements: a fieldset brings its own border and padding.
		<div
			role="group"
			id={sub.id}
			data-slot="menu-sheet-sub-content"
			className={cn("border-b border-border-subtle pl-7", className, "w-full min-w-0 max-w-none")}
			{...props}
		/>
	);
}

export {
	MenuSheet,
	MenuSheetCheckboxItem,
	type MenuSheetCheckboxItemProps,
	MenuSheetContent,
	type MenuSheetContentProps,
	MenuSheetGroup,
	MenuSheetItem,
	type MenuSheetItemProps,
	MenuSheetLabel,
	MenuSheetRadioGroup,
	MenuSheetRadioItem,
	type MenuSheetRadioItemProps,
	MenuSheetSeparator,
	MenuSheetSub,
	MenuSheetSubContent,
	MenuSheetSubTrigger,
	sheetContentProps,
	useMenuSheet,
};
