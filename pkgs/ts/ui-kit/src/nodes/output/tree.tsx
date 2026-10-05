// TreeRef -- nested rows that fold, on the kit Tree.
//
// Server-owned nodes, browser-owned moment. The nodes are a flat list, each
// `{key, parent, label}` plus optional `icon` and `badge`; siblings keep the
// order they arrive in, and a parent nobody ships puts its child at the top so
// nothing goes missing. Which rows are open and which is selected live in
// props too, so the browser sets them as you click and a server write
// overrides them: one copy, whoever wrote last wins. Every write is a plain
// merge (`nodes`, `selected`, `expanded`), so the type needs no handlers.
//
// Outbound, one notify per intent on the tree's own path, the intent named in
// `event` (the server's `on_*` each take one):
//
//   {event: "select", key}            a click or Space
//   {event: "open", key}              Enter or a double click
//   {event: "toggle", key, open}      a fold or an unfold
//   {event: "rename", key, title}     needs `editable`
//   {event: "move", key, parent, index}  needs `draggable`; parent "" is the top
//
// The browser never edits the nodes. A rename or a move is a request the
// server answers with the nodes as they now are.

import { OPS } from "@nustackdev/ui-core";
import { Edit3 } from "lucide-react";
import { useCallback, useMemo } from "react";
import { Badge } from "../../components/ui/badge";
import { ContextMenuItem } from "../../components/ui/context-menu";
import { EmptyState } from "../../components/ui/empty-state";
import { Tree, TreeItem } from "../../components/ui/tree";
import type { TreeMove, TreeSource } from "../../components/ui/tree-model";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useListProp,
	useSend,
	useSetProps,
	useStringProp,
} from "../../tree";

/** One node as the wire ships it, read defensively. */
type WireNode = { key: string; parent: string; label: string; icon: string; badge: string };

function str(v: unknown): string {
	return v == null ? "" : String(v);
}

function readNodes(raw: readonly unknown[]): WireNode[] {
	const out: WireNode[] = [];
	for (const r of raw) {
		if (r == null || typeof r !== "object" || Array.isArray(r)) continue;
		const n = r as Record<string, unknown>;
		const key = str(n.key);
		if (!key) continue;
		out.push({
			key,
			parent: str(n.parent),
			label: n.label == null ? key : str(n.label),
			icon: str(n.icon),
			badge: str(n.badge),
		});
	}
	return out;
}

const NO_KEYS: string[] = [];

function TreeView({ path }: NodeProps) {
	const label = useStringProp(path, "label", "Tree");
	const editable = useBoolProp(path, "editable");
	const draggable = useBoolProp(path, "draggable");
	const selected = useStringProp(path, "selected");
	const rawNodes = useListProp<unknown>(path, "nodes");
	const rawExpanded = useListProp<unknown>(path, "expanded");
	const setProps = useSetProps(path);
	const send = useSend(path);

	const nodes = useMemo(() => readNodes(rawNodes), [rawNodes]);
	const byKey = useMemo(() => new Map(nodes.map((n) => [n.key, n])), [nodes]);
	const expandedKeys = useMemo(
		() => (rawExpanded.length ? rawExpanded.map(str) : NO_KEYS),
		[rawExpanded],
	);
	const expanded = useMemo(() => new Set(expandedKeys), [expandedKeys]);

	const source = useMemo<TreeSource>(() => {
		const kids = new Map<string, string[]>();
		const roots: string[] = [];
		for (const n of nodes) {
			if (n.parent && n.parent !== n.key && byKey.has(n.parent)) {
				const list = kids.get(n.parent);
				if (list) list.push(n.key);
				else kids.set(n.parent, [n.key]);
			} else {
				roots.push(n.key);
			}
		}
		return { roots, childrenOf: (key) => kids.get(key) ?? NO_KEYS };
	}, [nodes, byKey]);

	const notify = useCallback(
		(event: string, fields: Record<string, unknown>) => send(OPS.notify, { event, ...fields }),
		[send],
	);

	const onToggle = useCallback(
		(key: string, open: boolean) => {
			const next = open ? [...expandedKeys, key] : expandedKeys.filter((k) => k !== key);
			setProps({ expanded: next });
			notify("toggle", { key, open });
		},
		[expandedKeys, setProps, notify],
	);

	const onSelect = useCallback(
		(key: string) => {
			setProps({ selected: key });
			notify("select", { key });
		},
		[setProps, notify],
	);

	const onActivate = useCallback((key: string) => notify("open", { key }), [notify]);

	const onRename = useCallback(
		(key: string, title: string) => notify("rename", { key, title }),
		[notify],
	);

	const onMove = useCallback(
		(m: TreeMove) => notify("move", { key: m.key, parent: m.parent ?? "", index: m.index }),
		[notify],
	);

	return (
		<Tree
			aria-label={label}
			source={source}
			expanded={expanded}
			onToggle={onToggle}
			selectedKey={selected || null}
			onSelect={onSelect}
			onActivate={onActivate}
			onRename={editable ? onRename : undefined}
			onMove={draggable ? onMove : undefined}
			empty={<EmptyState size="sm">Nothing here</EmptyState>}
			renderItem={(item) => {
				const node = byKey.get(item.row.key);
				const title = node?.label ?? item.row.key;
				return (
					<TreeItem
						item={item}
						title={title}
						icon={node?.icon ? <span aria-hidden="true">{node.icon}</span> : undefined}
						label={
							node?.badge ? (
								<span className="flex min-w-0 flex-1 items-center gap-2">
									<span className="min-w-0 flex-1 truncate">{title}</span>
									<Badge variant="outline" size="sm" className="shrink-0">
										{node.badge}
									</Badge>
								</span>
							) : undefined
						}
						menu={
							editable ? (
								<ContextMenuItem onSelect={item.startRename}>
									<Edit3 />
									Rename
								</ContextMenuItem>
							) : undefined
						}
					/>
				);
			}}
		/>
	);
}

export const TreeRef: NodeEntry = { component: TreeView };
