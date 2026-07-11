import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { TagInput } from "./tag-input";

const SIZES = ["sm", "md", "lg"] as const;

function Controlled({
	size,
	initial = ["react", "typescript"],
	invalid,
	disabled,
}: {
	size?: "sm" | "md" | "lg";
	initial?: string[];
	invalid?: boolean;
	disabled?: boolean;
}) {
	const [tags, setTags] = useState<string[]>(initial);
	return (
		<TagInput
			size={size}
			invalid={invalid}
			disabled={disabled}
			value={tags}
			onValueChange={setTags}
			placeholder="Add a tag..."
		/>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-md">
				<Controlled />
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 max-w-md space-y-6">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						sizes
					</div>
					<div className="space-y-3">
						{SIZES.map((s) => (
							<div key={s}>
								<div className="mb-1 font-mono text-xs text-text-muted">{s}</div>
								<Controlled size={s} />
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						states
					</div>
					<div className="space-y-3">
						<Controlled initial={[]} />
						<Controlled disabled />
						<Controlled invalid />
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/TagInput",
};

export default meta;
