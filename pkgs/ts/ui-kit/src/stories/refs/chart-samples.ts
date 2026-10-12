// The chart samples, as Python ships them.
//
// chart-samples.json is written by the nustd test that checks the builders
// (tests/nustd/ui/test_chart.py, UPDATE_CHART_SAMPLES=1): per sample, the
// props a typed builder's slot declares and the merge patch its `set(data)`
// sends. So what the stories draw is what a program draws, not a copy.

import type { ChainStep, Props, TreeFrame } from "@nustackdev/ui-core";
import { type ChartOption, mergeOption } from "../../lib/chart/option";
import samples from "./chart-samples.json";

export type SampleName = keyof typeof samples;

type Sample = { props: Props & { option: ChartOption; height?: number }; patch: ChartOption };

export function sample(name: SampleName): Sample {
	return samples[name] as unknown as Sample;
}

/** The chain level a slot declares: a `Chart` node with the builder's props. */
export function chartStep(segment: string, name: SampleName, props: Props = {}): ChainStep {
	return [segment, "Chart", { ...sample(name).props, ...props }];
}

/** The frame `set(data)` sends for the sample. */
export function chartSet(ref: string[], name: SampleName): TreeFrame {
	return { op: "merge", ref, payload: sample(name).patch };
}

/** The option as drawn after `set(data)`: for the primitive, no store. */
export function sampleOption(name: SampleName): ChartOption {
	const s = sample(name);
	return mergeOption(s.props.option, s.patch);
}
