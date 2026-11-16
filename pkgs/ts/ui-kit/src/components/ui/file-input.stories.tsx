import type { Meta, StoryObj } from "@storybook/react-vite";
import { type ReactNode, useId, useState } from "react";
import { Label } from "./field";
import { FileInput, type FileInputFile, FileRow, type FileState } from "./file-input";

// Both themes: the toolbar's theme switch, like every other story.

const SIZES = ["sm", "md", "lg"] as const;
const noop = () => {};

function Caption({ children }: { children: ReactNode }) {
	return (
		<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
			{children}
		</div>
	);
}

export const Zone: StoryObj = {
	render: () => (
		<div className="max-w-xl space-y-8 p-8">
			<div>
				<Caption>sizes</Caption>
				<div className="space-y-3">
					{SIZES.map((s) => (
						<div key={s} className="grid grid-cols-[4rem_1fr] items-center gap-3">
							<div className="font-mono text-xs text-text-muted">{s}</div>
							<FileInput size={s} accept=".csv" maxSize={20_000_000} onFiles={noop} />
						</div>
					))}
				</div>
			</div>
			<div>
				<Caption>states</Caption>
				<div className="space-y-3">
					<FileInput onFiles={noop} />
					<FileInput invalid accept="image/*" onFiles={noop} />
					<FileInput readOnly onFiles={noop} />
					<FileInput disabled accept=".pdf" maxSize={5_000_000} onFiles={noop} />
				</div>
			</div>
			<div>
				<Caption>hint and prompt</Caption>
				<div className="space-y-3">
					<FileInput multiple accept=".csv,.tsv,application/json" onFiles={noop} />
					<FileInput hint="One page scans work best" accept=".pdf" onFiles={noop} />
					<FileInput hint="" prompt="Drop the export here" onFiles={noop} />
				</div>
			</div>
		</div>
	),
};

const ROWS: { name: string; size: number; state: FileState; error?: string }[] = [
	{ name: "orders.csv", size: 48_213, state: "picked" },
	{ name: "photo.jpg", size: 3_481_002, state: "pulling" },
	{ name: "config.toml", size: 812, state: "landed" },
	{ name: "dump.sql", size: 1_204_331_009, state: "failed", error: "network" },
	{ name: "ledger.xlsx", size: 90_211, state: "failed", error: "unreadable" },
	{
		name: "quarterly-revenue-by-region-and-product-line-final-final-v3-reviewed.csv",
		size: 999_999,
		state: "picked",
	},
];

export const Rows: StoryObj = {
	render: () => (
		<div className="max-w-sm space-y-8 p-8">
			<div>
				<Caption>each state</Caption>
				<ul className="flex flex-col">
					{ROWS.map((r) => (
						<FileRow key={r.name} {...r} onRemove={noop} />
					))}
				</ul>
			</div>
			<div>
				<Caption>disabled, no remove</Caption>
				<ul className="flex flex-col">
					<FileRow name="orders.csv" size={48_213} disabled onRemove={noop} />
					<FileRow name="config.toml" size={812} state="landed" />
				</ul>
			</div>
		</div>
	),
};

/** A stand-in file of `size` bytes, for rows that start filled. */
const fake = (name: string, size: number, type = "") =>
	new File([new Uint8Array(size)], name, { type });

const asFile = (f: File, state: FileState = "picked"): FileInputFile => ({
	name: f.name,
	size: f.size,
	state,
});

export const SingleFile: StoryObj = {
	render: function Render() {
		const id = useId();
		const [file, setFile] = useState<File | null>(null);
		const [refused, setRefused] = useState("");
		return (
			<div className="max-w-sm space-y-8 p-8">
				<div className="flex flex-col gap-1">
					<Label htmlFor={id}>Orders</Label>
					<FileInput
						id={id}
						accept=".csv"
						maxSize={20_000_000}
						file={file ? asFile(file) : null}
						onRemove={() => setFile(null)}
						onFiles={(fit, out) => {
							setRefused(out.map((f) => f.name).join(", "));
							if (fit[0]) setFile(fit[0]);
						}}
					/>
					{refused ? <p className="text-xs text-status-danger">Not a CSV: {refused}</p> : null}
				</div>
				<div>
					<Caption>picked, each size</Caption>
					<div className="space-y-3">
						{SIZES.map((s) => (
							<FileInput
								key={s}
								size={s}
								file={{ name: "orders.csv", size: 48_213 }}
								onRemove={noop}
								onFiles={noop}
							/>
						))}
					</div>
				</div>
				<div>
					<Caption>picked, states</Caption>
					<div className="space-y-3">
						<FileInput
							file={{ name: "photo.jpg", size: 3_481_002, state: "pulling" }}
							onRemove={noop}
							onFiles={noop}
						/>
						<FileInput
							file={{ name: "ledger.xlsx", size: 90_211, state: "failed", error: "unreadable" }}
							onRemove={noop}
							onFiles={noop}
						/>
						<FileInput
							invalid
							file={{ name: "orders.csv", size: 48_213 }}
							onRemove={noop}
							onFiles={noop}
						/>
						<FileInput
							readOnly
							file={{ name: "orders.csv", size: 48_213, state: "landed" }}
							onFiles={noop}
						/>
						<FileInput
							disabled
							file={{ name: "orders.csv", size: 48_213 }}
							onRemove={noop}
							onFiles={noop}
						/>
					</div>
				</div>
			</div>
		);
	},
};

export const MultipleFiles: StoryObj = {
	render: function Render() {
		const id = useId();
		const [files, setFiles] = useState<{ id: number; file: File }[]>(() => [
			{ id: 1, file: fake("orders.csv", 48_213, "text/csv") },
			{ id: 2, file: fake("notes.md", 2_140, "text/markdown") },
			{ id: 3, file: fake("photo.jpg", 348_100, "image/jpeg") },
		]);
		return (
			<div className="flex max-w-sm flex-col gap-1 p-8">
				<Label htmlFor={id}>Attachments</Label>
				<FileInput
					id={id}
					multiple
					maxSize={50_000_000}
					onFiles={(fit) =>
						setFiles((was) => [...was, ...fit.map((file) => ({ id: Math.random(), file }))])
					}
				/>
				{files.length > 0 ? (
					<ul className="flex flex-col">
						{files.map(({ id: key, file }) => (
							<FileRow
								key={key}
								name={file.name}
								size={file.size}
								onRemove={() => setFiles((was) => was.filter((x) => x.id !== key))}
							/>
						))}
					</ul>
				) : null}
			</div>
		);
	},
};

const meta: Meta<typeof FileInput> = {
	title: "UI/FileInput",
	component: FileInput,
	tags: ["autodocs"],
};

export default meta;
