// Per-Ref-type state slice factories.
//
// Each entry corresponds to one Python Ref class on the nudle side
// (api/src/nudle/refs.py) and to one renderer in src/renderers/.
// Adding a new Ref type means: add a factory here, add a renderer in the
// registry, add the Python Ref class. Nothing else changes.

export type RefSlice = {
	type: string;
	value: unknown;
	// One method per op the Ref type accepts.
	write?: (value: unknown) => void;
	append?: (value: unknown) => void;
};

// Setter is the zustand store's `set` -- passed in so factories don't
// have to import the store and create a cycle. Each factory builds a
// closure over the ref's path and the setter.
export type Setter = (mutator: (refs: Record<string, RefSlice>) => void) => void;

export type SliceFactory = (path: string, set: Setter) => RefSlice;

const titleRef: SliceFactory = (path, set) => ({
	type: "TitleRef",
	value: "",
	write: (v) =>
		set((refs) => {
			refs[path].value = v as string;
		}),
});

const intRef: SliceFactory = (path, set) => ({
	type: "IntRef",
	value: 0,
	write: (v) =>
		set((refs) => {
			refs[path].value = v as number;
		}),
});

type LineChartValue = { points: [number, number][] };

const lineChart: SliceFactory = (path, set) => ({
	type: "LineChart",
	value: { points: [] } as LineChartValue,
	write: (v) =>
		set((refs) => {
			refs[path].value = v as LineChartValue;
		}),
	append: (v) =>
		set((refs) => {
			const cur = refs[path].value as LineChartValue;
			cur.points.push(v as [number, number]);
		}),
});

export const factories: Record<string, SliceFactory> = {
	TitleRef: titleRef,
	IntRef: intRef,
	LineChart: lineChart,
};
