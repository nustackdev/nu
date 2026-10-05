import type { Meta, StoryObj } from "@storybook/react-vite";
import { Edit3, Ellipsis, FileText, Folder, FolderOpen, Plus, Trash2 } from "lucide-react";
import { useMemo, useRef, useState } from "react";
import { ContextMenuItem, ContextMenuSeparator } from "./context-menu";
import { EmptyState } from "./empty-state";
import { IconButton } from "./icon-button";
import { Tree, type TreeHandle, TreeItem } from "./tree";
import type { TreeMove, TreeSource } from "./tree-model";

// An in-memory file tree that takes the tree's intents the way an app would:
// the kit reports, this applies, the tree redraws from what comes back.

type Node = { title: string; folder: boolean; children: string[] };
type Files = Record<string, Node>;

const SEED: Files = {
	root: { title: "", folder: true, children: ["src", "docs", "README.md", "package.json"] },
	src: { title: "src", folder: true, children: ["app.tsx", "lib", "styles.css"] },
	lib: { title: "lib", folder: true, children: ["tree.ts", "roving.ts", "utils.ts"] },
	"app.tsx": { title: "app.tsx", folder: false, children: [] },
	"styles.css": { title: "styles.css", folder: false, children: [] },
	"tree.ts": { title: "tree.ts", folder: false, children: [] },
	"roving.ts": { title: "roving.ts", folder: false, children: [] },
	"utils.ts": { title: "utils.ts", folder: false, children: [] },
	docs: { title: "docs", folder: true, children: ["intro.md", "drafts"] },
	"intro.md": { title: "intro.md", folder: false, children: [] },
	drafts: { title: "drafts", folder: true, children: [] },
	"README.md": { title: "README.md", folder: false, children: [] },
	"package.json": { title: "package.json", folder: false, children: [] },
};

function parentOf(files: Files, key: string): string {
	return Object.keys(files).find((k) => files[k]?.children.includes(key)) ?? "root";
}

function move(files: Files, { key, parent, index }: TreeMove): Files {
	const next = structuredClone(files);
	const from = next[parentOf(next, key)];
	if (from) from.children = from.children.filter((k) => k !== key);
	next[parent ?? "root"]?.children.splice(index, 0, key);
	return next;
}

function useFiles() {
	const [files, setFiles] = useState<Files>(SEED);
	const source = useMemo<TreeSource>(
		() => ({
			roots: files.root?.children ?? [],
			childrenOf: (key) => files[key]?.children ?? [],
		}),
		[files],
	);
	return { files, setFiles, source };
}

function useFold(initial: string[] = []) {
	const [expanded, setExpanded] = useState<ReadonlySet<string>>(new Set(initial));
	const onToggle = (key: string, open: boolean) =>
		setExpanded((prev) => {
			const next = new Set(prev);
			if (open) next.add(key);
			else next.delete(key);
			return next;
		});
	return { expanded, onToggle };
}

const frame = "w-72 rounded-lg border border-border-default bg-bg-surface p-1.5";
const note = "mt-3 max-w-72 font-mono text-xs text-text-muted";

/** Everything on: icons, select, activate, rename, drag, actions, menu. */
function FileBrowser() {
	const { files, setFiles, source } = useFiles();
	const { expanded, onToggle } = useFold(["src"]);
	const [selected, setSelected] = useState<string | null>("app.tsx");
	const [log, setLog] = useState("Click, arrows, Enter, F2, drag, right-click");
	const tree = useRef<TreeHandle>(null);

	const remove = (key: string) =>
		setFiles((prev) => {
			const next = structuredClone(prev);
			const parent = next[parentOf(next, key)];
			if (parent) parent.children = parent.children.filter((k) => k !== key);
			return next;
		});

	return (
		<div className="p-8">
			<div className={frame}>
				<Tree
					ref={tree}
					aria-label="Files"
					source={source}
					expanded={expanded}
					onToggle={onToggle}
					selectedKey={selected}
					onSelect={setSelected}
					onActivate={(key) => setLog(`open ${files[key]?.title}`)}
					onRename={(key, title) => {
						setFiles((prev) => ({ ...prev, [key]: { ...(prev[key] as Node), title } }));
						setLog(`rename ${key} -> ${title}`);
					}}
					onMove={(m) => {
						setFiles((prev) => move(prev, m));
						if (m.parent) onToggle(m.parent, true);
						setLog(`move ${m.key} -> ${m.parent ?? "top"}[${m.index}]`);
					}}
					foldLeaves={false}
					renderEmptyBranch={() => "Empty folder"}
					empty={<EmptyState size="sm">No files</EmptyState>}
					renderItem={(item) => {
						const node = files[item.row.key];
						const title = node?.title ?? item.row.key;
						const Icon = node?.folder ? (item.row.expanded ? FolderOpen : Folder) : FileText;
						return (
							<TreeItem
								item={item}
								title={title}
								icon={<Icon />}
								actions={
									<>
										{node?.folder ? (
											<IconButton
												variant="ghost"
												size="sm"
												ring="inset"
												aria-label={`New in ${title}`}
											>
												<Plus />
											</IconButton>
										) : null}
										<IconButton
											variant="ghost"
											size="sm"
											ring="inset"
											aria-label={`More for ${title}`}
										>
											<Ellipsis />
										</IconButton>
									</>
								}
								menu={
									<>
										<ContextMenuItem onSelect={item.startRename}>
											<Edit3 />
											Rename
										</ContextMenuItem>
										<ContextMenuSeparator />
										<ContextMenuItem variant="danger" onSelect={() => remove(item.row.key)}>
											<Trash2 />
											Delete
										</ContextMenuItem>
									</>
								}
							/>
						);
					}}
				/>
			</div>
			<div className={note}>{log}</div>
		</div>
	);
}

/** The least a tree takes: no icons, no rename, no drag. */
function Plain() {
	const { files, source } = useFiles();
	const { expanded, onToggle } = useFold();
	return (
		<div className="p-8">
			<div className={frame}>
				<Tree
					aria-label="Outline"
					source={source}
					expanded={expanded}
					onToggle={onToggle}
					renderItem={(item) => (
						<TreeItem item={item} title={files[item.row.key]?.title ?? item.row.key} />
					)}
				/>
			</div>
		</div>
	);
}

/** Every row folds, leaf or not (Notion's pages); selection follows focus. */
function LeavesFold() {
	const { files, source } = useFiles();
	const { expanded, onToggle } = useFold(["docs"]);
	const [selected, setSelected] = useState<string | null>(null);
	return (
		<div className="p-8">
			<div className={frame}>
				<Tree
					aria-label="Pages"
					source={source}
					expanded={expanded}
					onToggle={onToggle}
					selectedKey={selected}
					onSelect={setSelected}
					selectionFollowsFocus
					foldLeaves
					renderEmptyBranch={() => "No pages inside"}
					renderItem={(item) => (
						<TreeItem
							item={item}
							title={files[item.row.key]?.title ?? item.row.key}
							icon={<FileText />}
						/>
					)}
				/>
			</div>
			<div className={note}>selected: {selected ?? "none"}</div>
		</div>
	);
}

const meta: Meta = {
	title: "UI/Tree",
};

export default meta;

export const Files: StoryObj = { render: () => <FileBrowser /> };
export const Minimal: StoryObj = { render: () => <Plain /> };
export const FoldingLeaves: StoryObj = { render: () => <LeavesFold /> };
