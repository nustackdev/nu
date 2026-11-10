// CalendarHeatmapRef -- display-only year of days, a shade per day.
//
// Server-owned. A write is a partial merge of the props, which is the default
// store behaviour, so there is no handler. `values` is replaced whole: day
// `YYYY-MM-DD` to a count or to named counts ({jobs, builds}). Read-time
// coercion keeps a bad payload from breaking the page. Composes the kit
// CalendarHeatmap primitive.

import { CalendarHeatmap } from "../../components/ui/calendar-heatmap";
import type { CalendarHeatmapValues } from "../../components/ui/calendar-heatmap-model";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useEnumProp,
	useNumberProp,
	useProp,
	useStringProp,
} from "../../tree";

const NO_VALUES: CalendarHeatmapValues = {};

function asValues(v: unknown): CalendarHeatmapValues {
	return v && typeof v === "object" && !Array.isArray(v) ? (v as CalendarHeatmapValues) : NO_VALUES;
}

function CalendarHeatmapView({ path }: NodeProps) {
	const values = asValues(useProp<unknown>(path, "values", null));
	const end = useStringProp(path, "end");
	const weeks = useNumberProp(path, "weeks", 53);
	const weekStart = useEnumProp(path, "week_start", ["mon", "sun"] as const, "mon");
	const tone = useEnumProp(path, "tone", ["accent", "accent-2"] as const, "accent");
	const title = useStringProp(path, "title");
	const unit = useStringProp(path, "unit");
	const suffix = useStringProp(path, "suffix");
	const peakLabel = useStringProp(path, "peak_label", "Busiest");
	const showTotals = useBoolProp(path, "show_totals", true);
	const showLegend = useBoolProp(path, "show_legend", true);
	return (
		<CalendarHeatmap
			values={values}
			end={end || undefined}
			weeks={weeks > 0 ? weeks : 53}
			weekStart={weekStart}
			tone={tone}
			title={title}
			unit={unit}
			suffix={suffix}
			peakLabel={peakLabel}
			showTotals={showTotals}
			showLegend={showLegend}
		/>
	);
}

export const CalendarHeatmapRef: NodeEntry = { component: CalendarHeatmapView };
