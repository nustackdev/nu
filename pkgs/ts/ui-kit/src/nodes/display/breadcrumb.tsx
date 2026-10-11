// BreadcrumbRef -- the trail to here, from `items` of {label, href}. STUB:
// the smallest honest draw with the Breadcrumb primitive, the last crumb as
// the current page; the display unit owns navigation and the setters.

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

type Crumb = { label?: unknown; href?: unknown };

function BreadcrumbView({ path }: NodeProps) {
	const items = useListProp<Crumb>(path, "items");
	return (
		<Breadcrumb>
			<BreadcrumbList>
				{items.map((item, i) => {
					const label = item?.label == null ? "" : String(item.label);
					const last = i === items.length - 1;
					return (
						<Fragment key={`${i}-${label}`}>
							<BreadcrumbItem>
								{last ? (
									<BreadcrumbPage>{label}</BreadcrumbPage>
								) : (
									<BreadcrumbLink href={item?.href == null ? undefined : String(item.href)}>
										{label}
									</BreadcrumbLink>
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
