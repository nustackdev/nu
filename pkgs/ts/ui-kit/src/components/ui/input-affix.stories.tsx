import type { Meta, StoryObj } from "@storybook/react-vite";
import { AtSign } from "lucide-react";
import { useState } from "react";
import { InputAffix, PasswordInput, SearchInput } from "./input-affix";

const SIZES = ["sm", "md", "lg"] as const;

function Search({ size, initial = "" }: { size?: (typeof SIZES)[number]; initial?: string }) {
	const [value, setValue] = useState(initial);
	return (
		<SearchInput
			size={size}
			aria-label="Search"
			placeholder="Search projects..."
			value={value}
			onChange={(e) => setValue(e.target.value)}
			onClear={() => setValue("")}
		/>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-xl space-y-3">
			<Search initial="nustd" />
			<PasswordInput aria-label="Password" defaultValue="correct horse" />
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 max-w-xl space-y-6">
			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					sizes
				</div>
				<div className="space-y-3">
					{SIZES.map((s) => (
						<div key={s} className="grid grid-cols-[4rem_1fr_1fr] items-center gap-3">
							<div className="font-mono text-xs text-text-muted">{s}</div>
							<Search size={s} initial="query" />
							<PasswordInput size={s} aria-label={`Password ${s}`} defaultValue="hunter2" />
						</div>
					))}
				</div>
			</div>

			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					states
				</div>
				<div className="space-y-3">
					<InputAffix leading={<AtSign />} aria-label="Handle" placeholder="handle" />
					<SearchInput aria-label="Disabled" value="disabled" disabled onClear={() => {}} />
					<SearchInput aria-label="Read only" value="read only" readOnly onClear={() => {}} />
					<PasswordInput aria-label="Invalid" invalid defaultValue="short" />
					<PasswordInput aria-label="Disabled password" disabled defaultValue="secret" />
				</div>
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/InputAffix",
};

export default meta;
