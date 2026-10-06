import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { Code } from "./code";
import { Markdown } from "./markdown";

const SEED = `# Heading one

A paragraph of body text. **Bold**, *italic*, \`inline code\` and a
[link](https://nustack.dev).

## Heading two

- a list item
- another one
  - nested

1. first
2. second

- [ ] a checklist item
- [x] a done one

> A quote, for the left rule and the slant.

| Ref | Kind | Reads | Note |
| :--- | :---: | ---: | --- |
| **MarkdownRef** | input | 1284 | the value is \`markdown\` |
| *CodeRef* | input | 421 | [docs](https://nustack.dev) |
| \`TableRef\` | display | 3120 | a \\| pipe, escaped |

\`\`\`python
def fence(lang):
    return f"a {lang} code fence"
\`\`\`

#### Heading four

---

A last paragraph, so the bottom edge has something to sit on.
`;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-3xl">
			<Markdown value={SEED} />
		</div>
	),
};

type Args = { readOnly: boolean; placeholder: string; showSource: boolean };

function Playground({ readOnly, placeholder, showSource }: Args) {
	const [value, setValue] = useState(SEED);
	return (
		<div className="p-8 max-w-3xl space-y-6">
			<Markdown value={value} placeholder={placeholder} readOnly={readOnly} onCommit={setValue} />
			{showSource && (
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						committed markdown
					</div>
					<Code block language="markdown" value={value} />
				</div>
			)}
		</div>
	);
}

export const Editor: StoryObj<Args> = {
	args: { readOnly: false, placeholder: "Write, or type # for a heading", showSource: true },
	render: (args) => <Playground {...args} />,
};

export const Empty: StoryObj = {
	render: () => (
		<div className="p-8 max-w-3xl">
			<Markdown value="" readOnly={false} placeholder="Write, or type # for a heading" />
		</div>
	),
};

const FENCES = `Fences are drawn by the same engine as a \`Code\` block.

\`\`\`python
def fence(lang: str) -> str:
    return f"a {lang} code fence"  # comment
\`\`\`

\`\`\`ts
export const add = (a: number, b: number): number => a + b;
\`\`\`

\`\`\`sql
SELECT name, count(*) FROM refs WHERE kind = 'code' GROUP BY name;
\`\`\`

\`\`\`shell
uv venv --python 3.10 && uv pip install nucli
\`\`\`

\`\`\`nulang
an unknown language renders plain, and keeps its name
\`\`\`

\`\`\`
no language at all
\`\`\`
`;

function FencesSideBySide() {
	const [value, setValue] = useState(FENCES);
	return (
		<div className="grid grid-cols-1 gap-8 p-8 lg:grid-cols-2">
			<div>
				<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
					read-only
				</div>
				<Markdown value={value} />
			</div>
			<div>
				<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
					editable
				</div>
				<Markdown value={value} readOnly={false} onCommit={setValue} />
			</div>
		</div>
	);
}

export const Fences: StoryObj = {
	render: () => <FencesSideBySide />,
};

const TABLES = `GFM tables: type \`| a | b |\` and press Enter for a new one. Tab moves between
cells, Enter goes down a cell. The handles on the row and column under the pointer
(or the caret) add, move, align and delete; Shift+F10 and Alt+Shift+F10 open their menus.

| Run | Model | Tokens | Status | Latency |
| --- | --- | ---: | :---: | ---: |
| \`run_142\` | gpt-5 | 1284 | **ok** | 820ms |
| \`run_141\` | gpt-5-mini | 421 | ok | 180ms |
| \`run_140\` | claude-4.7 | 3120 | *warn* | 3.4s |
| \`run_139\` | [gpt-5](https://nustack.dev) | 640 | a \\| b |  |

| Only a header |
| --- |
`;

function TablesSideBySide() {
	const [value, setValue] = useState(TABLES);
	return (
		<div className="space-y-8 p-8">
			<div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						read-only
					</div>
					<Markdown value={value} />
				</div>
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						editable
					</div>
					<Markdown value={value} readOnly={false} onCommit={setValue} />
				</div>
			</div>
			<div>
				<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
					committed markdown
				</div>
				<Code block language="markdown" value={value} />
			</div>
		</div>
	);
}

export const Tables: StoryObj = {
	render: () => <TablesSideBySide />,
};

const meta: Meta = {
	title: "UI/Markdown",
};

export default meta;
