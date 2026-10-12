// Chart -- the one chart node. Draws an ECharts option.
//
// Server-owned. Props are `option` (the whole ECharts option, plain data),
// `height` and `max_points` (the window a streamed series keeps). A line, a
// pie or a sankey is the same node with a different option: the typed charts
// are Python builders that produce one, so a new chart type needs no code
// here.
//
// Four handlers, the generic set every chart shares:
//   write   {option?, height?, max_points?}: `option` replaces the whole
//           option and draws it from scratch.
//   merge   a partial option, applied the way ECharts' setOption merges
//           (components matched by id, then name, then the first free slot).
//   append  {series, points}: points onto one series (an index, id or name;
//           an unknown name adds a series styled like the last one), kept to
//           the newest `max_points`.
//   clear   {series?}: empty one series' data, or every series'.
// A click on a data item notifies {event: "click", series, series_index,
// name, index, value}.
//
// Appended points do not go through the store: they land in a ring per
// series (./stream) and reach the chart as one patch per animation frame.
// The store keeps the option, so a remount or a theme switch draws the
// option with the rings' points swapped in.

import { OPS } from "@nustackdev/ui-core";
import { useCallback, useEffect, useMemo, useRef } from "react";
import { Chart, type ChartClick, type ChartHandle } from "../../components/ui/chart";
import {
	type ChartOption,
	findSeries,
	isPlain,
	mergeOption,
	seriesOf,
	seriesWithData,
	withSeriesData,
} from "../../lib/chart/option";
import { type NodeEntry, type NodeProps, pathKey, useProps, useSend } from "../../tree";
import {
	disposeStream,
	dropSeries,
	listen,
	peekStream,
	pushPoints,
	resizeStream,
	streamData,
} from "./stream";

const DEFAULTS = { height: 256, max_points: 500 };
const NO_OPTION: ChartOption = {};

function _option(v: unknown): ChartOption {
	return isPlain(v) ? v : NO_OPTION;
}

function _map(v: unknown): Record<string, unknown> {
	return isPlain(v) ? v : {};
}

function _height(v: unknown): number {
	const n = Number(v);
	return Number.isFinite(n) && n >= 16 ? Math.floor(n) : DEFAULTS.height;
}

function _cap(v: unknown): number {
	const n = Number(v);
	return Number.isFinite(n) && n >= 1 ? Math.floor(n) : DEFAULTS.max_points;
}

function _data(option: ChartOption, index: number): unknown[] {
	const d = seriesOf(option)[index]?.data;
	return Array.isArray(d) ? d : [];
}

function ChartView({ path }: NodeProps) {
	const props = useProps(path);
	const option = _option(props.option);
	const height = _height(props.height);
	const key = pathKey(path);
	const handle = useRef<ChartHandle>(null);
	const send = useSend(path);

	// The rings are read at render, so whatever streamed before this mount
	// (or before the last option change) is drawn with it. `key` stands in for
	// `path`, compared by value.
	const composed = useMemo(() => withSeriesData(option, streamData(path)), [option, key]);

	useEffect(
		() =>
			listen(path, (dirty) => {
				const rings = peekStream(path)?.rings;
				if (!rings) return;
				const series: Record<string, unknown>[] = [];
				const last = Math.max(...dirty);
				for (let i = 0; i <= last; i++) {
					const ring = dirty.has(i) ? rings.get(i) : undefined;
					series.push(ring ? { data: ring.toArray() } : {});
				}
				handle.current?.patch({ series });
			}),
		[key],
	);

	const onPointClick = useCallback(
		(e: ChartClick) => send(OPS.notify, { event: "click", ...e }),
		[send],
	);

	return (
		<Chart
			ref={handle}
			option={composed}
			height={height}
			resetKey={props.revision}
			onPointClick={onPointClick}
		/>
	);
}

export const ChartNode: NodeEntry = {
	component: ChartView,
	fill: true,
	handlers: {
		write: (ctx, payload) => {
			const p = _map(payload);
			if ("option" in p) dropSeries(ctx.path);
			if ("max_points" in p) resizeStream(ctx.path, _cap(p.max_points));
			ctx.update((props) => {
				if ("option" in p) {
					props.option = _option(p.option);
					// Draw from scratch: a replaced option keeps nothing of the old.
					props.revision = (Number(props.revision) || 0) + 1;
				}
				if ("height" in p) props.height = _height(p.height);
				if ("max_points" in p) props.max_points = _cap(p.max_points);
			});
		},
		merge: (ctx, payload) => {
			if (!isPlain(payload)) return;
			const base = _option(ctx.store.getState().getIn(ctx.path)?.props.option);
			// A series the patch hands new data to is the option's again.
			dropSeries(ctx.path, seriesWithData(base, payload));
			ctx.update((props) => {
				props.option = mergeOption(_option(props.option), payload);
			});
		},
		append: (ctx, payload) => {
			const p = _map(payload);
			const points = Array.isArray(p.points) ? p.points : [];
			if (points.length === 0) return;
			const props = ctx.store.getState().getIn(ctx.path)?.props ?? {};
			const option = _option(props.option);
			const key = p.series ?? 0;
			let index = findSeries(option, key);
			let added: ChartOption | null = null;
			if (index < 0) {
				// Only a name can add a series; a position past the end names nothing.
				if (typeof key !== "string") return;
				const list = seriesOf(option);
				const { data: _d, id: _i, name: _n, ...style } = list[list.length - 1] ?? { type: "line" };
				index = list.length;
				added = { ...option, series: [...list, { ...style, name: key, data: [] }] };
			}
			pushPoints(ctx.path, index, points, _cap(props.max_points), _data(option, index));
			if (added) {
				const next = added;
				ctx.update((draft) => {
					draft.option = next;
				});
			}
		},
		clear: (ctx, payload) => {
			const key = _map(payload).series;
			const option = _option(ctx.store.getState().getIn(ctx.path)?.props.option);
			const list = seriesOf(option);
			const which =
				key == null ? list.map((_, i) => i) : [findSeries(option, key)].filter((i) => i >= 0);
			if (which.length === 0) return;
			dropSeries(ctx.path, which);
			ctx.update((props) => {
				props.option = {
					...option,
					series: list.map((s, i) => (which.includes(i) ? { ...s, data: [] } : s)),
				};
			});
		},
	},
	dispose: ({ path }) => disposeStream(path),
};
