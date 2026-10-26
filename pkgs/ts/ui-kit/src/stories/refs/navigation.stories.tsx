// Refs/Navigation: every kit link under an AnchorCatcher, moving a fake host
// through History. A plain click is a push, so the nav items light up for
// the page they name; Option+click (or Option+Enter) reaches the host rule
// as "alt", which this host only logs, the way nuspace opens a pane beside.
// Cmd-click, the _blank link and the external one stay the browser's.
//
// The host lives under /nav-demo, and Reset puts the frame back where
// Storybook loaded it.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { Button } from "../../components/ui/button";
import { AnchorCatcher, type AnchorRule, History, useEntry } from "../../tree";
import { NodeStage, sinkParameters, step } from "./harness";

const meta: Meta = {
	title: "Refs/Navigation",
	parameters: sinkParameters,
};

export default meta;

type Story = StoryObj;

const ROOT = "nav-demo";
const BASE = "/nav-demo";

function EntryReadout({ log, onReset }: { log: string[]; onReset: () => void }) {
	const entry = useEntry();
	return (
		<div className="flex flex-col gap-2 font-mono text-xs text-text-secondary">
			<div className="flex items-center gap-2">
				<Button size="sm" variant="secondary" onClick={() => History.back()}>
					Back
				</Button>
				<Button size="sm" variant="secondary" onClick={() => History.forward()}>
					Forward
				</Button>
				<Button size="sm" variant="ghost" onClick={onReset}>
					Reset
				</Button>
			</div>
			<span>
				entry: {entry.url} query: {JSON.stringify(entry.query)}
			</span>
			<span>rule: {log.length ? log.join(", ") : "nothing yet"}</span>
		</div>
	);
}

function FakeHost() {
	const [start] = useState(() => History.current().url);
	const [log, setLog] = useState<string[]>([]);
	const rule: AnchorRule = (href, gesture) => {
		setLog((l) => [...l.slice(-3), `${gesture} ${href}`]);
		if (gesture === "plain") History.push(href);
		// "alt" is handled too: a real host opens it beside.
		return true;
	};
	const col = [step(ROOT, "Column", { gap: 4 })];
	const nav = [...col, step("nav", "NavList", { variant: "horizontal", label: "Main" })];
	const links = [...col, step("links", "Row", { gap: 3, wrap: true, align: "center" })];
	return (
		<AnchorCatcher rule={rule}>
			<div className="flex flex-col gap-4">
				<EntryReadout log={log} onReset={() => History.replace(start)} />
				<NodeStage
					root={ROOT}
					label="Links under one AnchorCatcher"
					chains={[
						col,
						nav,
						[...nav, step("home", "NavItemRef", { label: "Home", href: BASE, exact: true })],
						[...nav, step("feed", "NavItemRef", { label: "Feed", href: `${BASE}/feed` })],
						[...nav, step("docs", "NavItemRef", { label: "Docs", href: `${BASE}/docs` })],
						[
							...col,
							step("crumbs", "BreadcrumbRef", {
								items: [
									{ label: "Home", href: BASE },
									{ label: "Docs", href: `${BASE}/docs` },
									{ label: "Spec", href: "https://nustack.dev", target: "_blank" },
									{ label: "Here" },
								],
							}),
						],
						links,
						[
							...links,
							step("text", "LinkRef", { href: `${BASE}/feed?tab=new`, label: "New in the feed" }),
						],
						[
							...links,
							step("button", "ButtonRef", { label: "Open docs", href: `${BASE}/docs/intro` }),
						],
						[
							...links,
							step("blank", "LinkRef", {
								href: `${BASE}/feed`,
								label: "Feed in a new tab",
								target: "_blank",
							}),
						],
						[
							...links,
							step("ext", "LinkRef", { href: "https://nustack.dev", label: "nustack.dev" }),
						],
						[
							...col,
							step("page", "PageLinkRef", {
								href: `${BASE}/docs`,
								title: "Docs",
								icon: "book-open",
								description: "A page link, routed like the rest",
							}),
						],
					]}
				/>
			</div>
		</AnchorCatcher>
	);
}

export const LinksAndCatcher: Story = {
	render: () => <FakeHost />,
};
