import type * as React from "react";
import { formatShortcut, keySpoken, type Platform } from "../../lib/shortcut";
import { cn } from "../../lib/utils";
import { Kbd, type KbdProps } from "./kbd";

// A key combination: key names in (`["mod", "K"]`), one `Kbd` out with the
// whole combination in it, spelled for the reader's platform
// (lib/shortcut.ts): `⌘⇧R` run together on a Mac, `Ctrl+Shift+R` elsewhere.
// `mod` is command on a Mac and control elsewhere, so one shortcut written
// once reads right on both.
//
// The glyphs are hidden from screen readers and the combination is said once,
// in words ("Command Shift R").

export interface ShortcutProps extends Omit<React.HTMLAttributes<HTMLElement>, "children"> {
	/** Key names, in the order they are held: modifiers first. */
	keys: readonly string[];
	variant?: KbdProps["variant"];
	size?: KbdProps["size"];
	/** Spell for this platform instead of the reader's. For docs and stories. */
	platform?: Platform;
}

export function Shortcut({ keys, variant, size, platform, className, ...props }: ShortcutProps) {
	return (
		<Kbd
			data-slot="shortcut"
			variant={variant}
			size={size}
			className={cn("shrink-0", className)}
			{...props}
		>
			<span aria-hidden="true">{formatShortcut(keys, platform)}</span>
			<span className="sr-only">{keys.map((k) => keySpoken(k, platform)).join(" ")}</span>
		</Kbd>
	);
}
