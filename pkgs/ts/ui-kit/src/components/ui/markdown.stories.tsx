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

const meta: Meta = {
	title: "UI/Markdown",
};

export default meta;
