import type { Meta, StoryObj } from "@storybook/react-vite";
import * as React from "react";
import { sinkParameters, ThemePair } from "../../stories/kitchen-sink/frame";
import { LevelMeter } from "./level-meter";

const STEPS = [0, 0.1, 0.35, 0.6, 0.85, 1];

/** A level that moves like speech, for the live row. */
function useTalk(): number {
	const [level, setLevel] = React.useState(0);
	React.useEffect(() => {
		const t0 = performance.now();
		const id = setInterval(() => {
			const t = (performance.now() - t0) / 1000;
			setLevel(Math.max(0, Math.sin(t * 5) * Math.sin(t * 1.3)) * 0.9);
		}, 60);
		return () => clearInterval(id);
	}, []);
	return level;
}

function Live() {
	return <LevelMeter level={useTalk()} />;
}

export const Levels: StoryObj = {
	render: () => (
		<ThemePair>
			<div className="flex flex-col gap-3">
				{STEPS.map((l) => (
					<div key={l} className="grid grid-cols-[4rem_1fr] items-center gap-3">
						<span className="font-mono text-xs text-text-muted">{l}</span>
						<LevelMeter level={l} />
					</div>
				))}
				<div className="grid grid-cols-[4rem_1fr] items-center gap-3">
					<span className="font-mono text-xs text-text-muted">quiet</span>
					<LevelMeter level={0.6} quiet />
				</div>
				<div className="grid grid-cols-[4rem_1fr] items-center gap-3">
					<span className="font-mono text-xs text-text-muted">live</span>
					<Live />
				</div>
				<div className="grid grid-cols-[4rem_1fr] items-center gap-3">
					<span className="font-mono text-xs text-text-muted">24 bars</span>
					<LevelMeter level={0.5} bars={24} />
				</div>
			</div>
		</ThemePair>
	),
};

const meta: Meta = {
	title: "UI/LevelMeter",
	parameters: sinkParameters,
};

export default meta;
