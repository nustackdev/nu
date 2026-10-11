// Kitchen sink: tabs, links, disclosure and the tree, light and dark side by side.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { ChevronDown, FileText, Folder, FolderOpen, Home, Settings } from "lucide-react";
import { useMemo, useState } from "react";
import {
	Accordion,
	AccordionContent,
	AccordionItem,
	AccordionTrigger,
} from "../../components/ui/accordion";
import {
	Breadcrumb,
	BreadcrumbEllipsis,
	BreadcrumbItem,
	BreadcrumbLink,
	BreadcrumbList,
	BreadcrumbPage,
	BreadcrumbSeparator,
} from "../../components/ui/breadcrumb";
import { Button } from "../../components/ui/button";
import {
	Collapsible,
	CollapsibleContent,
	CollapsibleTrigger,
} from "../../components/ui/collapsible";
import { NavLink } from "../../components/ui/nav-link";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { Text } from "../../components/ui/text";
import { Tree, TreeItem } from "../../components/ui/tree";
import type { TreeSource } from "../../components/ui/tree-model";
import { Block, Row, SinkPage, ThemePair, sinkParameters } from "./frame";

const TAB_VARIANTS = ["line", "pill", "segmented"] as const;

function TabsRows() {
	return (
		<Block title="Tabs">
			{TAB_VARIANTS.map((variant) => (
				<Row key={variant} label={variant}>
					<Tabs defaultValue="runs">
						<TabsList variant={variant}>
							<TabsTrigger variant={variant} value="overview">
								Overview
							</TabsTrigger>
							<TabsTrigger variant={variant} value="runs">
								Runs
							</TabsTrigger>
							<TabsTrigger variant={variant} value="settings">
								<Settings />
								Settings
							</TabsTrigger>
							<TabsTrigger variant={variant} value="off" disabled>
								Disabled
							</TabsTrigger>
						</TabsList>
						<TabsContent value="runs">
							<Text size="sm" tone="secondary">
								Runs panel ({variant}).
							</Text>
						</TabsContent>
					</Tabs>
				</Row>
			))}
			<Row label="sizes">
				{(["sm", "md", "lg"] as const).map((size) => (
					<Tabs key={size} defaultValue="a">
						<TabsList variant="segmented">
							<TabsTrigger variant="segmented" size={size} value="a">
								{size}
							</TabsTrigger>
							<TabsTrigger variant="segmented" size={size} value="b">
								Other
							</TabsTrigger>
						</TabsList>
					</Tabs>
				))}
			</Row>
			<Row label="list only">
				<Tabs defaultValue="b">
					<TabsList variant="pill">
						<TabsTrigger value="a">Trigger without variant</TabsTrigger>
						<TabsTrigger value="b">Active</TabsTrigger>
					</TabsList>
				</Tabs>
			</Row>
		</Block>
	);
}

function Links() {
	return (
		<Block title="Links">
			{(["default", "underline"] as const).map((variant) => (
				<Row key={variant} label={`NavLink ${variant}`}>
					<NavLink variant={variant} href="#" active>
						<Home />
						Active
					</NavLink>
					<NavLink variant={variant} href="#">
						Inactive (hover me)
					</NavLink>
					<NavLink variant={variant} href="#" aria-disabled>
						Disabled
					</NavLink>
				</Row>
			))}
			<Row label="NavLink sizes">
				{(["sm", "md", "lg"] as const).map((size) => (
					<NavLink key={size} size={size} href="#" active={size === "md"}>
						{size}
					</NavLink>
				))}
			</Row>
			<Row label="Sidebar">
				<nav className="flex w-56 flex-col gap-0.5 rounded-lg border border-border-subtle bg-bg-surface p-1.5">
					<NavLink href="#" active className="w-full">
						Planes
					</NavLink>
					<NavLink href="#" className="w-full">
						Runs
					</NavLink>
					<NavLink href="#" className="w-full">
						Settings
					</NavLink>
				</nav>
			</Row>
			<Row label="Breadcrumb">
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
							<BreadcrumbLink href="#">Projects</BreadcrumbLink>
						</BreadcrumbItem>
						<BreadcrumbSeparator />
						<BreadcrumbItem>
							<BreadcrumbPage>nu</BreadcrumbPage>
						</BreadcrumbItem>
					</BreadcrumbList>
				</Breadcrumb>
			</Row>
		</Block>
	);
}

function Disclosure() {
	return (
		<Block title="Disclosure">
			<Row label="Accordion">
				<Accordion type="single" defaultValue="two" collapsible className="w-full max-w-md">
					<AccordionItem value="one">
						<AccordionTrigger>What is a plane?</AccordionTrigger>
						<AccordionContent>A running Nu program.</AccordionContent>
					</AccordionItem>
					<AccordionItem value="two">
						<AccordionTrigger>Open item</AccordionTrigger>
						<AccordionContent>
							<Text size="sm" tone="secondary">
								This one starts open, so its content and rotated chevron show.
							</Text>
						</AccordionContent>
					</AccordionItem>
					<AccordionItem value="three">
						<AccordionTrigger>Closed item</AccordionTrigger>
						<AccordionContent>Hidden.</AccordionContent>
					</AccordionItem>
				</Accordion>
			</Row>
			<Row label="Collapsible">
				<Collapsible defaultOpen className="w-full max-w-md">
					<CollapsibleTrigger asChild>
						<Button variant="ghost">
							Details
							<ChevronDown />
						</Button>
					</CollapsibleTrigger>
					<CollapsibleContent>
						<div className="mt-2 rounded-md border border-border-subtle bg-bg-sunken p-3">
							<Text size="sm">Open collapsible content.</Text>
						</div>
					</CollapsibleContent>
				</Collapsible>
			</Row>
		</Block>
	);
}

type Node = { title: string; children: string[] };

const FILES: Record<string, Node> = {
	src: { title: "src", children: ["app.tsx", "lib", "styles.css"] },
	"app.tsx": { title: "app.tsx", children: [] },
	lib: { title: "lib", children: ["tree.ts"] },
	"tree.ts": { title: "tree.ts", children: [] },
	"styles.css": { title: "styles.css", children: [] },
	docs: { title: "docs", children: ["intro.md"] },
	"intro.md": { title: "intro.md", children: [] },
	"README.md": { title: "README.md", children: [] },
};
const ROOTS = ["src", "docs", "README.md"];
const FOLDERS = new Set(["src", "lib", "docs"]);

function FileTree() {
	const [expanded, setExpanded] = useState<ReadonlySet<string>>(new Set(["src"]));
	const [selected, setSelected] = useState<string | null>("app.tsx");
	const source = useMemo<TreeSource>(
		() => ({ roots: ROOTS, childrenOf: (key) => FILES[key]?.children ?? [] }),
		[],
	);
	return (
		<div className="w-72 rounded-lg border border-border-default bg-bg-surface p-1.5">
			<Tree
				aria-label="Files"
				source={source}
				expanded={expanded}
				onToggle={(key, open) =>
					setExpanded((prev) => {
						const next = new Set(prev);
						if (open) next.add(key);
						else next.delete(key);
						return next;
					})
				}
				selectedKey={selected}
				onSelect={setSelected}
				renderItem={(item) => {
					const key = item.row.key;
					const Icon = FOLDERS.has(key) ? (item.row.expanded ? FolderOpen : Folder) : FileText;
					return (
						<TreeItem
							item={item}
							title={FILES[key]?.title ?? key}
							icon={<Icon />}
							highlighted={key === "styles.css"}
						/>
					);
				}}
			/>
		</div>
	);
}

function TreeRows() {
	return (
		<Block title="Tree">
			<Row label="Tree">
				<FileTree />
				<Text size="xs" tone="muted" mono className="max-w-48">
					src expanded, app.tsx selected, styles.css highlighted.
				</Text>
			</Row>
		</Block>
	);
}

export const Default: StoryObj = {
	name: "Navigation",
	render: () => (
		<SinkPage title="Navigation" description="Tabs, links, breadcrumbs, disclosure and the tree.">
			<ThemePair>
				<TabsRows />
				<Links />
				<Disclosure />
				<TreeRows />
			</ThemePair>
		</SinkPage>
	),
};

const meta: Meta = {
	title: "Kitchen Sink/Navigation",
	parameters: sinkParameters,
};

export default meta;
