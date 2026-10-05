import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { Code } from "./code";

const PYTHON = `from dataclasses import dataclass


@dataclass
class Movie:
    """One row on the shelf."""

    title: str
    year: int = 0
    watched: bool = False


def fib(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b  # the pair walks forward
    return a


print([fib(i) for i in range(10)], None, True)
`;

const SAMPLES: Record<string, string> = {
	python: PYTHON,
	typescript: `type Movie = { title: string; year: number };

export function latest(shelf: Movie[]): Movie | undefined {
	// newest first, ties keep their order
	return [...shelf].sort((a, b) => b.year - a.year)[0];
}
`,
	sql: `SELECT title, year
FROM movies
WHERE watched = 0 AND year > 1990 -- recent, unseen
ORDER BY year DESC
LIMIT 10;
`,
	shell: `#!/usr/bin/env bash
uv venv --python 3.10 && uv pip install "nucli==0.5.5"
nu demo movies --port 8080  # serves the demo
`,
	markdown: `# Notes

Some **bold**, some *italic*, a [link](https://nustack.dev).

- one
- two
`,
};

const label = "mb-2 font-mono text-xs uppercase tracking-widest text-text-muted";

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
			Inline: <Code>const x = 42</Code>
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 max-w-2xl space-y-6">
			<div>
				<div className={label}>inline</div>
				<p className="text-sm text-text-primary">
					Reach for <Code>useState</Code> when a single value drives the surface;
					<Code>useReducer</Code> when transitions matter.
				</p>
			</div>
			<div>
				<div className={label}>block</div>
				<Code block language="tsx">
					{`import { Button } from "@nustackdev/ui-kit";

export function Save() {
  return <Button>Save</Button>;
}`}
				</Code>
			</div>
			<div>
				<div className={label}>block + copyable</div>
				<Code block copyable language="sh">
					{"npm install @nustackdev/ui-kit"}
				</Code>
			</div>
			<div>
				<div className={label}>block, editable</div>
				<Code block language="python" readOnly={false} value={PYTHON} />
			</div>
		</div>
	),
};

type Args = {
	language: keyof typeof SAMPLES;
	readOnly: boolean;
	lineNumbers: "auto" | "on" | "off";
	wrap: boolean;
	copyable: boolean;
	maxHeight: number;
};

function Playground({ language, readOnly, lineNumbers, wrap, copyable, maxHeight }: Args) {
	const [value, setValue] = useState(SAMPLES[language]);
	const [commits, setCommits] = useState(0);
	return (
		<div className="p-8 max-w-3xl space-y-3">
			<Code
				key={language}
				block
				value={value}
				language={language}
				readOnly={readOnly}
				lineNumbers={lineNumbers === "auto" ? undefined : lineNumbers === "on"}
				wrap={wrap}
				copyable={copyable}
				maxHeight={maxHeight}
				onCommit={(next) => {
					setValue(next);
					setCommits((n) => n + 1);
				}}
			/>
			<p className="text-sm text-text-muted">
				{readOnly
					? "Read-only. Flip readOnly in the controls; the same view becomes an editor."
					: `Editable. Cmd+enter or click away to commit. Commits so far: ${commits}.`}
			</p>
		</div>
	);
}

export const Editor: StoryObj<Args> = {
	args: {
		language: "python",
		readOnly: false,
		lineNumbers: "auto",
		wrap: false,
		copyable: true,
		maxHeight: 0,
	},
	argTypes: {
		language: { control: "select", options: Object.keys(SAMPLES) },
		lineNumbers: { control: "inline-radio", options: ["auto", "on", "off"] },
		maxHeight: { control: { type: "number", min: 0, step: 40 } },
	},
	render: (args) => <Playground {...args} />,
};

const meta: Meta = {
	title: "UI/Code",
};

export default meta;
