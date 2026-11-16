import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { FileDrop, FileRow, type FileState } from "./file-drop";

const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: function Render() {
		const [files, setFiles] = useState<{ id: number; file: File }[]>([]);
		return (
			<div className="w-96 p-8 space-y-2">
				<FileDrop
					multiple
					onFiles={(fit) =>
						setFiles((was) => [...was, ...fit.map((file) => ({ id: Math.random(), file }))])
					}
				/>
				<ul className="flex flex-col">
					{files.map(({ id, file }) => (
						<FileRow
							key={id}
							name={file.name}
							size={file.size}
							onRemove={() => setFiles((was) => was.filter((x) => x.id !== id))}
						/>
					))}
				</ul>
			</div>
		);
	},
};

const ROWS: { name: string; size: number; state: FileState; error?: string }[] = [
	{ name: "orders.csv", size: 48_213, state: "picked" },
	{ name: "photo.jpg", size: 3_481_002, state: "pulling" },
	{ name: "config.toml", size: 812, state: "landed" },
	{ name: "dump.sql", size: 1_204_331_009, state: "failed", error: "network" },
	{ name: "ledger.xlsx", size: 90_211, state: "failed", error: "unreadable" },
];

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6">
			{SIZES.map((s) => (
				<div key={s} className="w-96 space-y-2">
					<div className="font-mono text-xs uppercase tracking-widest text-text-muted">{s}</div>
					<FileDrop size={s} onFiles={() => {}} />
				</div>
			))}
			<div className="w-96 space-y-2">
				<div className="font-mono text-xs uppercase tracking-widest text-text-muted">
					invalid, read only, disabled
				</div>
				<FileDrop invalid onFiles={() => {}} />
				<FileDrop readOnly prompt="Read only" onFiles={() => {}} />
				<FileDrop disabled onFiles={() => {}} />
			</div>
			<ul className="flex w-96 flex-col">
				{ROWS.map((r) => (
					<FileRow key={r.name} {...r} onRemove={() => {}} />
				))}
			</ul>
		</div>
	),
};

const meta: Meta = {
	title: "UI/FileDrop",
};

export default meta;
