// BreadcrumbRef -- the trail to here, crumbs of {label, href}.
//
// Server-owned. A write replaces `items`, which is the default store
// behaviour, so this type is a component and nothing else. Python ships
// every crumb as a dict; a bare string still reads as a crumb with that
// label, so a term written as is draws too. Composes the kit Breadcrumb
// parts: the last crumb is the current page, a crumb with no href is plain
// text, and links act like LinkRef's: same tab, with the external mark when
// the href points at another host.

import { ExternalLink } from "lucide-react";
import { Fragment } from "react";
import {
	Breadcrumb,
	BreadcrumbItem,
	BreadcrumbLink,
	BreadcrumbList,
	BreadcrumbPage,
	BreadcrumbSeparator,
} from "../../components/ui/breadcrumb";
import { type NodeEntry, type NodeProps, useListProp } from "../../tree";

type Crumb = { label: string; href: string };

function toCrumb(raw: unknown): Crumb | null {
	if (typeof raw === "string") return { label: raw, href: "" };
	if (raw == null || typeof raw !== "object") return null;
	const { label, href } = raw as { label?: unknown; href?: unknown };
	return { label: label == null ? "" : String(label), href: href == null ? "" : String(href) };
}

function isCrossHost(href: string): boolean {
	if (href === "") return false;
	try {
		const url = new URL(href, window.location.href);
		return url.host !== "" && url.host !== window.location.host;
	} catch {
		return false;
	}
}

function BreadcrumbView({ path }: NodeProps) {
	const crumbs = useListProp<unknown>(path, "items")
		.map(toCrumb)
		.filter((c): c is Crumb => c !== null);
	if (crumbs.length === 0) return null;
	return (
		<Breadcrumb>
			<BreadcrumbList>
				{crumbs.map((crumb, i) => {
					const last = i === crumbs.length - 1;
					return (
						<Fragment key={`${i}-${crumb.label}`}>
							<BreadcrumbItem>
								{last ? (
									<BreadcrumbPage>{crumb.label}</BreadcrumbPage>
								) : crumb.href ? (
									<BreadcrumbLink href={crumb.href} className="inline-flex items-center gap-1">
										{crumb.label}
										{isCrossHost(crumb.href) ? (
											<ExternalLink aria-hidden="true" className="size-3 shrink-0" />
										) : null}
									</BreadcrumbLink>
								) : (
									<span>{crumb.label}</span>
								)}
							</BreadcrumbItem>
							{last ? null : <BreadcrumbSeparator />}
						</Fragment>
					);
				})}
			</BreadcrumbList>
		</Breadcrumb>
	);
}

export const BreadcrumbRef: NodeEntry = { component: BreadcrumbView };
