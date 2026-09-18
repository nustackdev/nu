import type { Meta, StoryObj } from "@storybook/react-vite";
import { RadioGroup, RadioGroupItem } from "./radio-group";

const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<RadioGroup defaultValue="one">
					<label className="flex items-center gap-2">
						<RadioGroupItem value="one" />
						<span className="text-sm text-text-primary">Option one</span>
					</label>
					<label className="flex items-center gap-2">
						<RadioGroupItem value="two" />
						<span className="text-sm text-text-primary">Option two</span>
					</label>
					<label className="flex items-center gap-2">
						<RadioGroupItem value="three" />
						<span className="text-sm text-text-primary">Option three</span>
					</label>
				</RadioGroup>
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						sizes
					</div>
					<div className="flex items-start gap-8">
						{SIZES.map((s) => (
							<div key={s}>
								<div className="mb-2 font-mono text-xs text-text-muted">{s}</div>
								<RadioGroup defaultValue="a">
									<label className="flex items-center gap-2">
										<RadioGroupItem size={s} value="a" />
										<span className="text-sm text-text-primary">A</span>
									</label>
									<label className="flex items-center gap-2">
										<RadioGroupItem size={s} value="b" />
										<span className="text-sm text-text-primary">B</span>
									</label>
								</RadioGroup>
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						states
					</div>
					<RadioGroup defaultValue="on">
						<label className="flex items-center gap-2">
							<RadioGroupItem value="off" />
							<span className="text-sm text-text-secondary">off</span>
						</label>
						<label className="flex items-center gap-2">
							<RadioGroupItem value="on" />
							<span className="text-sm text-text-secondary">on</span>
						</label>
						<label className="flex items-center gap-2">
							<RadioGroupItem value="disabled" disabled />
							<span className="text-sm text-text-secondary">disabled</span>
						</label>
						<label className="flex items-center gap-2">
							<RadioGroupItem value="invalid" invalid />
							<span className="text-sm text-text-secondary">invalid</span>
						</label>
					</RadioGroup>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/RadioGroup",
};

export default meta;
