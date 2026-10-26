// Button looks off the wire: how a node's `variant` and `size` props name a
// kit Button.
//
// ButtonRef (with or without an href) and an EmptyState's way out both
// draw the Button primitive, so they read its look the same way: the
// wire's `primary` is the kit's `default`, `danger` its `destructive`, and an
// unknown variant or size falls back to the default rather than to no look.

import type { ButtonProps } from "../components/ui/button";

export type ButtonVariant = NonNullable<ButtonProps["variant"]>;
export type ButtonSize = NonNullable<ButtonProps["size"]>;

/** Wire variant -> kit Button variant. */
export const VARIANT_TO_KIT: Record<string, ButtonVariant> = {
	primary: "default",
	secondary: "secondary",
	outline: "outline",
	ghost: "ghost",
	soft: "soft",
	danger: "destructive",
	link: "link",
};

export const BUTTON_SIZES: readonly ButtonSize[] = ["xs", "sm", "md", "lg"];

/** A wire variant as a kit one; unknown reads as the primary look. */
export function kitVariant(v: string): ButtonVariant {
	return VARIANT_TO_KIT[v] ?? "default";
}
