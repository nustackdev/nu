import type { Meta, StoryObj } from "@storybook/react-vite";
import { Stat, StatDelta, StatLabel, StatValue } from "./stat";

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<Stat>
					<StatLabel>Runs today</StatLabel>
					<StatValue>1,284</StatValue>
					<StatDelta direction="up">+ 12.4%</StatDelta>
				</Stat>
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-4 max-w-4xl">
				<Stat>
					<StatLabel>Runs today</StatLabel>
					<StatValue>1,284</StatValue>
					<StatDelta direction="up">+ 12.4%</StatDelta>
				</Stat>
				<Stat>
					<StatLabel>Tokens spent</StatLabel>
					<StatValue>842k</StatValue>
					<StatDelta direction="down">- 3.1%</StatDelta>
				</Stat>
				<Stat>
					<StatLabel>Error rate</StatLabel>
					<StatValue>0.9%</StatValue>
					<StatDelta direction="down" invert>
						- 0.2 pp
					</StatDelta>
				</Stat>
				<Stat>
					<StatLabel>Uptime</StatLabel>
					<StatValue>99.94%</StatValue>
					<StatDelta direction="flat">no change</StatDelta>
				</Stat>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Stat",
};

export default meta;
