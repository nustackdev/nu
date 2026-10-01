import type * as React from "react";
import { type Platform, keyLabel, keySpoken } from "../../lib/shortcut";
import { cn } from "../../lib/utils";
import { Kbd, type KbdProps } from "./kbd";

// A key combination: key names in (`["mod", "K"]`), one `Kbd` cap per key out,
// spelled for the reader's platform (lib/shortcut.ts). `mod` is command on a
// Mac and control elsewhere, so one shortcut written once reads right on both.
//
// The caps are hidden from screen readers and the combination is said once,
// in words ("Command K"). `ghost` caps sit tight, so `⌘K` in an input reads
// as one hint; `default` caps keep a hairline apart, like keys on a board.

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
		<kbd
			data-slot="shortcut"
			className={cn(
				"inline-flex items-center font-sans",
				variant === "ghost" ? "gap-px" : "gap-0.5",
				className,
			)}
			{...props}
		>
			{keys.map((k, i) => (
				<Kbd
					// biome-ignore lint/suspicious/noArrayIndexKey: a key may repeat; position is its identity
					key={i}
					variant={variant}
					size={size}
					aria-hidden="true"
				>
					{keyLabel(k, platform)}
				</Kbd>
			))}
			<span className="sr-only">{keys.map((k) => keySpoken(k, platform)).join(" ")}</span>
		</kbd>
	);
}
