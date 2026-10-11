// Shared layout for the kitchen sink pages: every page shows its content
// twice, light on the left and dark on the right.
//
// ThemePair renders the children twice in the same document. The page's
// <html> is pinned light (see `sinkParameters`), and the right column carries
// `.dark`, which re-resolves every token for its subtree. Anything that
// portals to <body> escapes that subtree, so overlays use FramePair instead:
// one iframe per theme, each a whole document with its own <html> class.

import type * as React from "react";
import { Heading } from "../../components/ui/heading";
import { Text } from "../../components/ui/text";
import { cn } from "../../lib/utils";

/** Story parameters every page shares: html pinned light, no padding. */
export const sinkParameters = {
	layout: "fullscreen",
	themes: { themeOverride: "light" },
};

function Column({ theme, children }: { theme: "light" | "dark"; children: React.ReactNode }) {
	return (
		<div
			data-sink-theme={theme}
			className={cn(
				"min-w-0 bg-bg-canvas px-8 py-8 text-text-primary",
				theme === "dark" && "dark",
			)}
		>
			<Text size="xs" tone="muted" mono className="mb-6 uppercase tracking-widest">
				{theme}
			</Text>
			<div className="flex flex-col gap-10">{children}</div>
		</div>
	);
}

/** Children twice, side by side: light left, dark right. */
export function ThemePair({ children }: { children: React.ReactNode }) {
	return (
		<div className="grid min-h-screen grid-cols-2">
			<Column theme="light">{children}</Column>
			<Column theme="dark">{children}</Column>
		</div>
	);
}

/** A page title over the pair, so a screenshot says what it is. */
export function SinkPage({
	title,
	description,
	children,
}: {
	title: string;
	description?: string;
	children: React.ReactNode;
}) {
	return (
		<div className="bg-bg-canvas text-text-primary">
			<div className="border-b border-border-subtle px-8 py-6">
				<Heading as="h1" size="3xl">
					{title}
				</Heading>
				{description ? (
					<Text size="sm" tone="secondary" className="mt-1">
						{description}
					</Text>
				) : null}
			</div>
			{children}
		</div>
	);
}

/** A titled group of rows. */
export function Block({ title, children }: { title: string; children: React.ReactNode }) {
	return (
		<section className="flex flex-col">
			<Heading as="h2" size="xl" className="mb-2">
				{title}
			</Heading>
			<div className="flex flex-col">{children}</div>
		</section>
	);
}

/** One labelled row: mono label left, items right. */
export function Row({
	label,
	children,
	className,
}: {
	label: string;
	children: React.ReactNode;
	className?: string;
}) {
	return (
		<div className="grid grid-cols-[9rem_1fr] items-start gap-4 border-b border-border-subtle py-3">
			<Text as="div" size="xs" tone="muted" mono className="pt-1.5">
				{label}
			</Text>
			<div className={cn("flex min-w-0 flex-wrap items-center gap-3", className)}>{children}</div>
		</div>
	);
}

/** One story, in a frame per theme, side by side. For content that portals. */
export function FramePair({
	storyId,
	height,
	label,
}: {
	storyId: string;
	height: number;
	label: string;
}) {
	return (
		<div className="flex flex-col gap-2">
			<Text size="xs" tone="muted" mono className="px-8">
				{label}
			</Text>
			<div className="grid grid-cols-2 border-y border-border-subtle">
				<StoryFrame storyId={storyId} theme="light" height={height} title={`${label}, light`} />
				<StoryFrame storyId={storyId} theme="dark" height={height} title={`${label}, dark`} />
			</div>
		</div>
	);
}

function StoryFrame({
	storyId,
	theme,
	height,
	title,
}: {
	storyId: string;
	theme: "light" | "dark";
	height: number;
	title: string;
}) {
	const src = `iframe.html?id=${storyId}&viewMode=story&globals=theme:${theme}`;
	return (
		<div style={{ height }} className="min-w-0">
			<iframe src={src} title={title} className="block size-full border-0" />
		</div>
	);
}
