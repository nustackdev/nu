import type { Meta, StoryObj } from "@storybook/react-vite";
import { Slash } from "lucide-react";
import { Fragment } from "react";
import {
	Breadcrumb,
	BreadcrumbEllipsis,
	BreadcrumbItem,
	BreadcrumbLink,
	BreadcrumbList,
	BreadcrumbPage,
	BreadcrumbSeparator,
} from "./breadcrumb";

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<Breadcrumb>
					<BreadcrumbList>
						<BreadcrumbItem>
							<BreadcrumbLink href="#">Home</BreadcrumbLink>
						</BreadcrumbItem>
						<BreadcrumbSeparator />
						<BreadcrumbItem>
							<BreadcrumbLink href="#">Projects</BreadcrumbLink>
						</BreadcrumbItem>
						<BreadcrumbSeparator />
						<BreadcrumbItem>
							<BreadcrumbPage>nu</BreadcrumbPage>
						</BreadcrumbItem>
					</BreadcrumbList>
				</Breadcrumb>
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6">
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						chevron
					</div>
					<Breadcrumb>
						<BreadcrumbList>
							<BreadcrumbItem>
								<BreadcrumbLink href="#">Home</BreadcrumbLink>
							</BreadcrumbItem>
							<BreadcrumbSeparator />
							<BreadcrumbItem>
								<BreadcrumbLink href="#">Projects</BreadcrumbLink>
							</BreadcrumbItem>
							<BreadcrumbSeparator />
							<BreadcrumbItem>
								<BreadcrumbPage>nu</BreadcrumbPage>
							</BreadcrumbItem>
						</BreadcrumbList>
					</Breadcrumb>
				</div>

				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						custom separator (slash)
					</div>
					<Breadcrumb>
						<BreadcrumbList>
							<BreadcrumbItem>
								<BreadcrumbLink href="#">Home</BreadcrumbLink>
							</BreadcrumbItem>
							<BreadcrumbSeparator>
								<Slash />
							</BreadcrumbSeparator>
							<BreadcrumbItem>
								<BreadcrumbLink href="#">Projects</BreadcrumbLink>
							</BreadcrumbItem>
							<BreadcrumbSeparator>
								<Slash />
							</BreadcrumbSeparator>
							<BreadcrumbItem>
								<BreadcrumbPage>nu</BreadcrumbPage>
							</BreadcrumbItem>
						</BreadcrumbList>
					</Breadcrumb>
				</div>

				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						with ellipsis
					</div>
					<Breadcrumb>
						<BreadcrumbList>
							<BreadcrumbItem>
								<BreadcrumbLink href="#">Home</BreadcrumbLink>
							</BreadcrumbItem>
							<BreadcrumbSeparator />
							<BreadcrumbItem>
								<BreadcrumbEllipsis />
							</BreadcrumbItem>
							<BreadcrumbSeparator />
							<BreadcrumbItem>
								<BreadcrumbPage>Details</BreadcrumbPage>
							</BreadcrumbItem>
						</BreadcrumbList>
					</Breadcrumb>
				</div>
			</div>
	),
};

const DEEP = ["Home", "Workspaces", "nustack", "Projects", "Mobile", "Navigation"];

// A deep trail, built from Fragments the way a mapped one is. Wide, every
// crumb shows; under 28rem of its own width (a phone, a strip column) the
// middle folds: Home > ... > Mobile > Navigation. Three crumbs never fold.
export const Deep: StoryObj = {
	render: () => (
		<div className="space-y-6 p-4">
			{[DEEP, DEEP.slice(0, 4), DEEP.slice(0, 3)].map((trail) => (
				<Breadcrumb key={trail.length}>
					<BreadcrumbList>
						{trail.map((crumb, i) => (
							<Fragment key={crumb}>
								<BreadcrumbItem>
									{i === trail.length - 1 ? (
										<BreadcrumbPage>{crumb}</BreadcrumbPage>
									) : (
										<BreadcrumbLink href="#">{crumb}</BreadcrumbLink>
									)}
								</BreadcrumbItem>
								{i === trail.length - 1 ? null : <BreadcrumbSeparator />}
							</Fragment>
						))}
					</BreadcrumbList>
				</Breadcrumb>
			))}
		</div>
	),
};

const meta: Meta = {
	title: "UI/Breadcrumb",
};

export default meta;
