// AvatarRef -- an image for a person or thing, initials when there is none.
//
// Server-owned. A write is a partial merge of `src` / `name` / `size` into
// the node's props, which is the default store behaviour, so this type is a
// component and nothing else. Composes the kit Avatar primitive: the image
// paints once it loads, and until then (or when it fails) the fallback shows
// up to two initials from `name`, or a person glyph when there is no name.
// The root carries `name` as its accessible name, so the image and the
// initials stay decorative. An unknown size reads as `md`.

import { User } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "../../components/ui/avatar";
import { cn } from "../../lib/utils";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";

type Size = "sm" | "md" | "lg" | "xl";

const SIZES: Record<string, Size> = { sm: "sm", md: "md", lg: "lg", xl: "xl" };

// Initials and the glyph grow with the disc, so a 48px avatar does not
// carry 24px type.
const INITIALS: Record<Size, string> = {
	sm: "text-xs",
	md: "text-xs",
	lg: "text-sm",
	xl: "text-base",
};

const GLYPH: Record<Size, string> = {
	sm: "size-3.5",
	md: "size-4",
	lg: "size-5",
	xl: "size-6",
};

// First and last word, or the one letter of a single word.
export function initials(name: string): string {
	const words = name.trim().split(/\s+/).filter(Boolean);
	if (words.length === 0) return "";
	if (words.length === 1) return Array.from(words[0])[0];
	return [words[0], words[words.length - 1]].map((w) => Array.from(w)[0]).join("");
}

function AvatarView({ path }: NodeProps) {
	const src = useStringProp(path, "src");
	const name = useStringProp(path, "name").trim();
	const size = SIZES[useStringProp(path, "size", "md")] ?? "md";
	const letters = initials(name);
	return (
		<Avatar
			size={size}
			role={name ? "img" : undefined}
			aria-label={name || undefined}
			aria-hidden={name ? undefined : true}
		>
			{src ? <AvatarImage src={src} alt="" /> : null}
			{/* The delay keeps initials from flashing while an image loads. */}
			<AvatarFallback delayMs={src ? 300 : undefined} aria-hidden="true" className={INITIALS[size]}>
				{letters || <User className={cn("text-text-muted", GLYPH[size])} />}
			</AvatarFallback>
		</Avatar>
	);
}

export const AvatarRef: NodeEntry = { component: AvatarView };
