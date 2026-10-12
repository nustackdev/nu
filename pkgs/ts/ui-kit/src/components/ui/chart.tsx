// Chart primitive. Draws one ECharts option, themed by the kit tokens.
//
// Design refs:
//   language/color.md   chart-1..8 in order, Tide sequential, diverging ramp
//   typography.md       tick labels: mono, xs, muted
//   palette.md          chart tooltip on the floating elevation
//
// Every chart type is the same component: what kind of chart it is lives in
// the option, so a new type is a new option and no new TypeScript. ECharts
// itself loads on first mount (lib/chart/load), the modular build for the
// typed set and the full one for anything past it, so a page with no chart
// pays nothing for it.
//
// The theme is read off the CSS tokens at the chart's own element and the
// chart re-inits when they change (a `.dark` toggle on <html>). ECharts 6
// has `setTheme`, but it still drops parts of a merged option on a switch,
// and a chart this size redraws from scratch within a frame.
//
// Updates come two ways. A new `option` prop merges into what is drawn,
// series replaced as a list (`resetKey` changing draws from scratch instead).
// The `patch` handle merges a partial option straight into the instance, no
// React render, which is what a stream of points goes through.

import * as React from "react";
import { type ECharts, type EChartsInstance, loadECharts } from "../../lib/chart/load";
import {
	type ChartOption,
	isPlain,
	mergeOption,
	needsFull,
	seriesOf,
} from "../../lib/chart/option";
import {
	type ChartTokens,
	chartTheme,
	readChartTokens,
	resolveVars,
	tokensKey,
} from "../../lib/chart/theme";
import { cn } from "../../lib/utils";

export type { ChartOption } from "../../lib/chart/option";

/** A click on a data item. JSON-safe, so a node can forward it as is. */
export type ChartClick = {
	series: string;
	series_index: number;
	name: string;
	index: number;
	value: unknown;
};

export interface ChartHandle {
	/** Merge a partial option into what is drawn, without a render. */
	patch: (option: ChartOption) => void;
}

export interface ChartProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "onClick"> {
	option: ChartOption;
	height?: number | string;
	/** Change it to draw the next option from scratch rather than merge it. */
	resetKey?: unknown;
	/** Load the full ECharts build even when the option would not need it. */
	full?: boolean;
	onPointClick?: (event: ChartClick) => void;
	ref?: React.Ref<ChartHandle>;
}

function reducedMotion(): boolean {
	return (
		typeof window !== "undefined" &&
		!!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
	);
}

// What the instance is actually handed: token vars resolved, aria on, kit
// motion timings, and an id on every series without one (its name when the
// name is unique, else its position). A `replaceMerge` on series keeps an
// existing series only when the ids match, names do not count, so without
// the id every new option rebuilt each series and replayed its entry
// animation instead of moving the old values to the new.
function prepare(el: Element | null, option: ChartOption): ChartOption {
	const resolved = resolveVars(el, option);
	const aria = isPlain(option.aria) ? option.aria : {};
	const out: ChartOption = {
		animationDuration: 280,
		animationDurationUpdate: 180,
		...resolved,
		aria: { enabled: true, ...aria },
	};
	if (option.series !== undefined) {
		const list = seriesOf(resolved);
		const names = list.map((s) => (s.name == null ? null : String(s.name)));
		const unique = (n: string | null) => n !== null && names.indexOf(n) === names.lastIndexOf(n);
		out.series = list.map((s, i) => {
			if (s.id != null) return s;
			const n = names[i];
			return { ...s, id: unique(n) ? `__n:${n}` : `__s${i}` };
		});
	}
	if (reducedMotion()) out.animation = false;
	return out;
}

function toClick(p: Record<string, unknown>): ChartClick {
	return {
		series: typeof p.seriesName === "string" ? p.seriesName : "",
		series_index: typeof p.seriesIndex === "number" ? p.seriesIndex : 0,
		name: typeof p.name === "string" ? p.name : String(p.name ?? ""),
		index: typeof p.dataIndex === "number" ? p.dataIndex : -1,
		value: p.value ?? null,
	};
}

export function Chart({
	option,
	height = 256,
	resetKey,
	full = false,
	onPointClick,
	className,
	style,
	ref,
	...props
}: ChartProps) {
	const el = React.useRef<HTMLDivElement>(null);
	const inst = React.useRef<EChartsInstance | null>(null);
	// What is drawn: the last option prop with every patch since merged in.
	// A re-init (theme switch) draws this, so streamed points survive it.
	const drawn = React.useRef<ChartOption>(option);
	const lastProp = React.useRef<ChartOption>(option);
	const lastReset = React.useRef(resetKey);
	const tokens = React.useRef<ChartTokens | null>(null);
	const onClick = React.useRef(onPointClick);
	onClick.current = onPointClick;

	const [lib, setLib] = React.useState<ECharts | null>(null);
	const [themeKey, setThemeKey] = React.useState("");
	// Once an option has needed the full build, stay on it: going back would
	// re-init for nothing, and the full build draws everything the modular does.
	const [wantFull, setWantFull] = React.useState(full || needsFull(option));
	if (!wantFull && (full || needsFull(option))) setWantFull(true);

	React.useImperativeHandle(
		ref,
		() => ({
			patch: (partial: ChartOption) => {
				drawn.current = mergeOption(drawn.current, partial);
				inst.current?.setOption(resolveVars(el.current, partial), {
					lazyUpdate: true,
					silent: true,
				});
			},
		}),
		[],
	);

	React.useEffect(() => {
		let live = true;
		loadECharts(wantFull).then(
			(l) => live && setLib(() => l),
			(err) => console.error("nu.ui: chart failed to load ECharts", err),
		);
		return () => {
			live = false;
		};
	}, [wantFull]);

	// Theme: read now, and again whenever <html> or <body> changes class or
	// style (how nudle and nuspace switch Dusk and Dawn), or the OS scheme
	// flips. Only a change in the resolved tokens re-inits.
	React.useLayoutEffect(() => {
		const node = el.current;
		if (!node) return;
		const read = () => {
			const t = readChartTokens(node);
			const key = tokensKey(t);
			tokens.current = t;
			setThemeKey((prev) => (prev === key ? prev : key));
		};
		read();
		const watch = new MutationObserver(read);
		const attributeFilter = ["class", "style", "data-theme"];
		watch.observe(document.documentElement, { attributes: true, attributeFilter });
		if (document.body) watch.observe(document.body, { attributes: true, attributeFilter });
		const scheme = window.matchMedia?.("(prefers-color-scheme: dark)");
		scheme?.addEventListener?.("change", read);
		return () => {
			watch.disconnect();
			scheme?.removeEventListener?.("change", read);
		};
	}, []);

	React.useEffect(() => {
		const node = el.current;
		if (!lib || !node || !tokens.current || !themeKey) return;
		const chart = lib.init(node, chartTheme(tokens.current), { renderer: "canvas" });
		inst.current = chart;
		chart.setOption(prepare(node, drawn.current), { notMerge: true });
		chart.on("click", (p) => {
			const params = p as unknown as Record<string, unknown>;
			if (params.componentType === "series") onClick.current?.(toClick(params));
		});
		return () => {
			chart.dispose();
			if (inst.current === chart) inst.current = null;
		};
	}, [lib, themeKey]);

	React.useEffect(() => {
		if (option === lastProp.current && resetKey === lastReset.current) return;
		const reset = resetKey !== lastReset.current;
		lastProp.current = option;
		lastReset.current = resetKey;
		drawn.current = option;
		inst.current?.setOption(
			prepare(el.current, option),
			reset ? { notMerge: true } : { replaceMerge: ["series"] },
		);
	}, [option, resetKey]);

	React.useEffect(() => {
		const node = el.current;
		if (!node || typeof ResizeObserver === "undefined") return;
		let frame = 0;
		const watch = new ResizeObserver(() => {
			cancelAnimationFrame(frame);
			frame = requestAnimationFrame(() => inst.current?.resize());
		});
		watch.observe(node);
		return () => {
			cancelAnimationFrame(frame);
			watch.disconnect();
		};
	}, []);

	return (
		<div
			ref={el}
			data-slot="chart"
			className={cn("w-full min-w-0", className)}
			style={{ height, ...style }}
			{...props}
		/>
	);
}
