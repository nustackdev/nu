// The kit's ECharts theme, read off the CSS tokens where the chart sits.
//
// ECharts draws to a canvas, so it cannot follow a CSS variable the way a
// styled element does: the colors have to be read out once and handed over
// as values. `readChartTokens` reads them with getComputedStyle on the
// chart's own element, so a chart inside a `.dark` subtree (the kitchen sink's
// dark column) gets Dusk while its neighbour gets Dawn. `chartTheme` turns
// them into an ECharts theme: the chart palette, muted mono tick labels at the
// xs step (typography.md, chart tick labels), subtle grid lines, and a tooltip
// dressed like the kit's own.

export type ChartTokens = {
	palette: string[];
	sequential: string[];
	diverging: string[];
	text: string;
	textSecondary: string;
	textMuted: string;
	borderSubtle: string;
	border: string;
	elevated: string;
	// What the chart is drawn over. Slices, cells and tiles are parted by a
	// line of this, so they read as gaps rather than outlines.
	ground: string;
	up: string;
	down: string;
	sans: string;
	mono: string;
};

// Dawn values, for a chart drawn where the kit stylesheet is not loaded (a
// test, a bare page). Same names as index.css.
const FALLBACK: ChartTokens = {
	palette: ["#0268a7", "#a67e1b", "#973069", "#2692b3", "#ae391b", "#1c9480", "#5d43ac", "#cb6f1d"],
	sequential: ["#acedf5", "#68d6ea", "#24bbdb", "#1d9cc0", "#157fa4", "#146387", "#29475c"],
	diverging: ["#1666aa", "#5e97cd", "#a2c6e6", "#dde0e5", "#e2b793", "#ca7d44", "#9c470e"],
	text: "#1a1d24",
	textSecondary: "#4e5158",
	textMuted: "#6a6d74",
	borderSubtle: "#e5e6e8",
	border: "#d9dadc",
	elevated: "#ffffff",
	ground: "#f9fafc",
	up: "#00713f",
	down: "#bb262c",
	sans: "Inter, ui-sans-serif, system-ui, sans-serif",
	mono: '"JetBrains Mono", ui-monospace, monospace',
};

function isTransparent(color: string): boolean {
	return color === "" || color === "transparent" || /rgba\(.*,\s*0\)$/.test(color);
}

// The first painted background at or above `el`.
function groundOf(el: Element): string {
	let cur: Element | null = el;
	while (cur) {
		const bg = getComputedStyle(cur).backgroundColor;
		if (!isTransparent(bg)) return bg;
		cur = cur.parentElement;
	}
	return "";
}

/** The chart tokens as they resolve at `el`. */
export function readChartTokens(el: Element): ChartTokens {
	const style = getComputedStyle(el);
	const read = (name: string, fallback: string) => style.getPropertyValue(name).trim() || fallback;
	const ramp = (prefix: string, n: number, fallback: string[]) =>
		Array.from({ length: n }, (_, i) => read(`--${prefix}-${i + 1}`, fallback[i]));
	return {
		palette: ramp("chart", 8, FALLBACK.palette),
		sequential: ramp("chart-seq", 7, FALLBACK.sequential),
		diverging: ramp("chart-div", 7, FALLBACK.diverging),
		text: read("--text-primary", FALLBACK.text),
		textSecondary: read("--text-secondary", FALLBACK.textSecondary),
		textMuted: read("--text-muted", FALLBACK.textMuted),
		borderSubtle: read("--border-subtle", FALLBACK.borderSubtle),
		border: read("--border-default", FALLBACK.border),
		elevated: read("--bg-elevated", FALLBACK.elevated),
		ground: groundOf(el) || read("--bg-canvas", FALLBACK.ground),
		up: read("--status-ok", FALLBACK.up),
		down: read("--status-danger", FALLBACK.down),
		sans: read("--font-display", FALLBACK.sans),
		mono: read("--font-mono", FALLBACK.mono),
	};
}

/** A string that changes exactly when the theme a chart would get does. */
export function tokensKey(tokens: ChartTokens): string {
	return JSON.stringify(tokens);
}

/** A `var(--name)` string resolved where the chart sits, anything else as is. */
export function resolveVar(el: Element | null, value: string): string {
	const m = /^var\(\s*(--[\w-]+)\s*(?:,\s*(.+))?\)$/.exec(value.trim());
	if (!m || !el) return value;
	return getComputedStyle(el).getPropertyValue(m[1]).trim() || m[2]?.trim() || value;
}

/**
 * The option with every `var(--x)` string swapped for its value at `el`, so a
 * server can color a series with a kit token. Data arrays of plain values are
 * skipped whole, which keeps a big series cheap.
 */
export function resolveVars<T>(el: Element | null, value: T): T {
	if (typeof value === "string")
		return (value.startsWith("var(") ? resolveVar(el, value) : value) as T;
	if (Array.isArray(value)) {
		if (value.length > 0 && typeof value[0] !== "object" && typeof value[0] !== "string")
			return value;
		let changed = false;
		const out = value.map((v) => {
			const r = resolveVars(el, v);
			if (r !== v) changed = true;
			return r;
		});
		return (changed ? out : value) as T;
	}
	if (typeof value === "object" && value !== null) {
		let changed = false;
		const out: Record<string, unknown> = {};
		for (const [k, v] of Object.entries(value)) {
			const r = resolveVars(el, v);
			if (r !== v) changed = true;
			out[k] = r;
		}
		return (changed ? out : value) as T;
	}
	return value;
}

/** The ECharts theme for these tokens. */
export function chartTheme(t: ChartTokens): Record<string, unknown> {
	// hideOverlap: a narrow chart drops tick labels rather than stacking them.
	const tick = { color: t.textMuted, fontFamily: t.mono, fontSize: 11, hideOverlap: true };
	const axisName = { color: t.textMuted, fontFamily: t.sans, fontSize: 11 };
	const axis = (splitLine: boolean) => ({
		axisLine: { show: true, lineStyle: { color: t.border } },
		axisTick: { show: false },
		axisLabel: tick,
		nameTextStyle: axisName,
		splitLine: { show: splitLine, lineStyle: { color: t.borderSubtle, type: [3, 3] } },
		splitArea: { show: false },
	});
	const value = axis(true);
	const parted = { borderColor: t.ground, borderWidth: 1 };
	return {
		color: t.palette,
		backgroundColor: "transparent",
		textStyle: { fontFamily: t.sans, color: t.textSecondary, fontSize: 12 },
		title: {
			left: 0,
			top: 0,
			textStyle: { color: t.text, fontFamily: t.sans, fontSize: 13, fontWeight: 600 },
			subtextStyle: { color: t.textMuted, fontFamily: t.sans, fontSize: 12 },
		},
		legend: {
			icon: "circle",
			itemWidth: 8,
			itemHeight: 8,
			itemGap: 14,
			textStyle: { color: t.textSecondary, fontFamily: t.sans, fontSize: 11 },
			inactiveColor: t.borderSubtle,
			pageTextStyle: { color: t.textMuted },
			pageIconColor: t.textSecondary,
			pageIconInactiveColor: t.borderSubtle,
		},
		tooltip: {
			// Matches the kit Tooltip: elevated surface, default border, the
			// floating shadow and sm radius. The tooltip is an element inside
			// the chart, so the shadow var resolves in its theme.
			backgroundColor: t.elevated,
			borderColor: t.border,
			borderWidth: 1,
			padding: [6, 10],
			textStyle: { color: t.text, fontFamily: t.sans, fontSize: 12 },
			extraCssText: "box-shadow: var(--elevation-floating); border-radius: var(--radius-sm, 4px);",
			axisPointer: {
				lineStyle: { color: t.border },
				crossStyle: { color: t.border },
				shadowStyle: { color: t.borderSubtle, opacity: 0.5 },
				label: { backgroundColor: t.elevated, color: t.text, fontFamily: t.mono, fontSize: 11 },
			},
		},
		categoryAxis: axis(false),
		valueAxis: value,
		timeAxis: value,
		logAxis: value,
		line: {
			symbol: "circle",
			symbolSize: 5,
			lineStyle: { width: 2 },
			emphasis: { lineStyle: { width: 2 } },
		},
		bar: {
			barMaxWidth: 32,
			label: { color: t.textSecondary, fontFamily: t.mono, fontSize: 11, textBorderWidth: 0 },
		},
		scatter: { symbolSize: 8, itemStyle: { opacity: 0.85 } },
		pie: {
			itemStyle: parted,
			label: { color: t.textSecondary, fontFamily: t.sans, fontSize: 11 },
			labelLine: { lineStyle: { color: t.border } },
		},
		// Labels sit on a fill, so they take the ground color: dark on Dusk's
		// light slots, light on Dawn's deep ones.
		funnel: { itemStyle: parted, label: { color: t.ground, fontFamily: t.sans, fontSize: 11 } },
		treemap: {
			itemStyle: { ...parted, gapWidth: 1 },
			label: { color: t.ground, fontFamily: t.sans, fontSize: 11 },
			upperLabel: { color: t.text, fontFamily: t.sans, fontSize: 11 },
			breadcrumb: {
				itemStyle: {
					color: t.elevated,
					borderColor: t.border,
					textStyle: { color: t.textSecondary },
				},
				emphasis: { itemStyle: { color: t.borderSubtle } },
			},
		},
		sunburst: { itemStyle: parted, label: { color: t.ground, fontFamily: t.sans, fontSize: 11 } },
		heatmap: { itemStyle: parted },
		sankey: {
			label: { color: t.textSecondary, fontFamily: t.sans, fontSize: 11 },
			lineStyle: { color: "gradient", opacity: 0.3 },
			itemStyle: { borderWidth: 0 },
		},
		gauge: {
			axisLine: { lineStyle: { color: [[1, t.borderSubtle]] } },
			splitLine: { lineStyle: { color: t.border } },
			axisTick: { lineStyle: { color: t.border } },
			axisLabel: tick,
			pointer: { itemStyle: { color: t.textSecondary } },
			anchor: { itemStyle: { color: t.textSecondary } },
			title: { color: t.textMuted, fontFamily: t.sans, fontSize: 12 },
			detail: { color: t.text, fontFamily: t.sans, fontWeight: 600 },
		},
		radar: {
			axisName: { color: t.textMuted, fontFamily: t.sans, fontSize: 11 },
			axisLine: { lineStyle: { color: t.borderSubtle } },
			splitLine: { lineStyle: { color: t.borderSubtle } },
			splitArea: { show: false },
			symbolSize: 4,
		},
		boxplot: { itemStyle: { color: t.ground, borderWidth: 1.5 } },
		candlestick: {
			itemStyle: { color: t.up, color0: t.down, borderColor: t.up, borderColor0: t.down },
		},
		visualMap: {
			// High to low, the order ECharts reads `color` in.
			color: [...t.sequential].reverse(),
			textStyle: { color: t.textMuted, fontFamily: t.mono, fontSize: 11 },
		},
		markLine: { lineStyle: { color: t.textMuted }, label: { color: t.textMuted } },
	};
}
