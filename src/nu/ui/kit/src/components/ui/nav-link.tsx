// NavLink primitive. Sidebar/nav-bar link that is active-aware.
//
// Design refs:
//   primitives.md    §NavLink (variants, sizes, states, asChild for router link)
//   palette.md       §2.4 accent-wash (active bg), §2.2 text tiers
//   space-radius.md  §Density Button (24/32/40 row map)
//   motion.md        §3 NavLink row (bg + color, duration-fast ease-out)
//   a11y.md          §4 aria-current="page" on active

import { cva, type VariantProps } from "class-variance-authority";
import { Slot as SlotPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

const navLinkVariants = cva(
	[
		"inline-flex items-center gap-2 whitespace-nowrap rounded-md",
		"font-medium",
		"transition-colors duration-fast ease-out",
		"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
		"[&_svg]:pointer-events-none [&_svg]:shrink-0",
		"aria-disabled:opacity-50 aria-disabled:pointer-events-none",
	].join(" "),
	{
		variants: {
			variant: {
				default: [
					"text-text-secondary hover:bg-bg-elevated hover:text-text-primary",
					// Active state driven by aria-current OR data-active so React
					// Router NavLink (which sets aria-current) and hand-wired active
					// props both work.
					"aria-[current=page]:bg-accent-wash aria-[current=page]:text-accent aria-[current=page]:font-medium",
					"data-[active=true]:bg-accent-wash data-[active=true]:text-accent data-[active=true]:font-medium",
				].join(" "),
				// Underline variant: minimal chrome, accent underline on active.
				underline: [
					"text-text-secondary hover:text-text-primary",
					"aria-[current=page]:text-text-primary aria-[current=page]:shadow-[inset_0_-2px_0_var(--accent)]",
					"data-[active=true]:text-text-primary data-[active=true]:shadow-[inset_0_-2px_0_var(--accent)]",
				].join(" "),
			},
			size: {
				sm: "h-6 px-2 text-sm [&_svg]:size-3.5",
				md: "h-8 px-3 text-lg [&_svg]:size-4",
				lg: "h-10 px-4 text-xl [&_svg]:size-4.5",
			},
		},
		defaultVariants: {
			variant: "default",
			size: "md",
		},
	},
);

export interface NavLinkProps
	extends React.AnchorHTMLAttributes<HTMLAnchorElement>,
		VariantProps<typeof navLinkVariants> {
	asChild?: boolean;
	// Active is a plain prop so consumers who resolve it from the router (e.g.
	// TanStack Router `useMatch`) can pass a boolean without hand-setting
	// aria-current. When true both aria-current="page" and data-active="true"
	// get emitted; primitives.md §NavLink notes this pairing.
	active?: boolean;
}

export function NavLink({
	className,
	variant,
	size,
	asChild = false,
	active,
	...props
}: NavLinkProps) {
	const Comp = asChild ? SlotPrimitive.Root : "a";
	return (
		<Comp
			data-slot="nav-link"
			data-active={active ? "true" : undefined}
			aria-current={active ? "page" : undefined}
			className={cn(navLinkVariants({ variant, size }), className)}
			{...props}
		/>
	);
}

export { navLinkVariants };
