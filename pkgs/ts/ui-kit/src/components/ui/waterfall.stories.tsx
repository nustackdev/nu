import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { Waterfall, type WaterfallSpan } from "./waterfall";

// One job: load, compute, write, nested two levels deep.
const trace: WaterfallSpan[] = [
	{ id: "job", label: "forecast job", start: 0, end: 1840, tone: "ok" },
	{ id: "load", parent: "job", label: "load inputs", start: 12, end: 420, tone: "ok" },
	{ id: "kv", parent: "load", label: "kv read orders", start: 18, end: 160, tone: "ok" },
	{
		id: "s3",
		parent: "load",
		label: "fetch fx rates",
		start: 22,
		end: 410,
		tone: "warn",
		detail: "retried once",
	},
	{ id: "fit", parent: "job", label: "fit model", start: 430, end: 1520, tone: "ok" },
	{ id: "f1", parent: "fit", label: "epoch 1", start: 440, end: 790, tone: "ok" },
	{ id: "f2", parent: "fit", label: "epoch 2", start: 795, end: 1150, tone: "ok" },
	{ id: "f3", parent: "fit", label: "epoch 3", start: 1155, end: 1510, tone: "ok" },
	{ id: "plot", parent: "job", label: "render chart", start: 1525, end: 1610, tone: "ok" },
	{
		id: "write",
		parent: "job",
		label: "write forecast",
		start: 1615,
		end: 1835,
		tone: "danger",
		detail: "kv write timed out",
	},
];

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-3xl">
			<Waterfall spans={trace} />
		</div>
	),
};

// Spans with no parent read as a sequence.
export const Sequential: StoryObj = {
	render: () => (
		<div className="p-8 max-w-3xl">
			<Waterfall
				spans={[
					{ id: "a", label: "checkout", start: 0, end: 3200, tone: "ok" },
					{ id: "b", label: "install deps", start: 3200, end: 41_000, tone: "ok" },
					{ id: "c", label: "typecheck", start: 41_000, end: 58_500, tone: "ok" },
					{ id: "d", label: "tests", start: 58_500, end: 132_000, tone: "danger" },
					{ id: "e", label: "deploy", start: 132_000, end: 140_000, tone: "neutral" },
				]}
			/>
		</div>
	),
};

// Work in flight: running spans have no end and draw to `now`.
export const Running: StoryObj = {
	render: () => (
		<div className="p-8 max-w-3xl">
			<Waterfall
				now={9000}
				end={12_000}
				spans={[
					{ id: "r", label: "hyperparameter sweep", start: 0, tone: "ok" },
					{ id: "t1", parent: "r", label: "trial lr=0.1", start: 200, end: 4100, tone: "ok" },
					{ id: "t2", parent: "r", label: "trial lr=0.01", start: 4200, tone: "ok" },
					{ id: "t3", parent: "r", label: "trial lr=0.001", start: 4300, tone: "info" },
				]}
			/>
		</div>
	),
};

export const Selectable: StoryObj = {
	render: function Render() {
		const [sel, setSel] = useState<string | null>("fit");
		return (
			<div className="p-8 max-w-3xl">
				<Waterfall spans={trace} selected={sel} onSelect={(s) => setSel(s.id)} />
			</div>
		);
	},
};

// A big trace: 600 spans past the 50 row cap, failures among the hidden
// ones, long labels, a minute-long window.
function bigTrace(): WaterfallSpan[] {
	const out: WaterfallSpan[] = [
		{
			id: "root",
			label: "nightly batch: rebuild every report in the warehouse",
			start: 0,
			end: 94_000,
			tone: "ok",
		},
	];
	let t = 100;
	for (let p = 0; p < 40; p++) {
		const pid = `p${p}`;
		const len = 1500 + ((p * 7919) % 2400);
		out.push({
			id: pid,
			parent: "root",
			label: `stage ${p + 1}: ${["ingest", "transform", "train", "export"][p % 4]}`,
			start: t,
			end: t + len,
			tone: p % 13 === 7 ? "danger" : "ok",
		});
		for (let c = 0; c < 14; c++) {
			const s = t + (c * len) / 14;
			out.push({
				id: `${pid}c${c}`,
				parent: pid,
				label: `task ${c + 1}`,
				start: s,
				end: s + len / 16,
				tone: (p * 14 + c) % 37 === 5 ? "danger" : (p + c) % 11 === 3 ? "warn" : "ok",
			});
		}
		t += len * 0.6;
	}
	return out;
}

export const PowerCase: StoryObj = {
	render: () => (
		<div className="p-8 max-w-4xl">
			<Waterfall spans={bigTrace()} labelWidth={240} />
		</div>
	),
};

const meta: Meta = {
	title: "UI/Waterfall",
};

export default meta;
