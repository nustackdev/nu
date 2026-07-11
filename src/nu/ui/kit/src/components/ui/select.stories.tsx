import type { Meta, StoryObj } from "@storybook/react-vite";
import {
	Select,
	SelectContent,
	SelectGroup,
	SelectItem,
	SelectLabel,
	SelectSeparator,
	SelectTrigger,
	SelectValue,
} from "./select";

const SIZES = ["sm", "md", "lg"] as const;
const VARIANTS = ["default", "ghost", "filled"] as const;

function BasicSelect(props: {
	size?: "sm" | "md" | "lg";
	variant?: "default" | "ghost" | "filled";
	invalid?: boolean;
	disabled?: boolean;
}) {
	return (
		<Select>
			<SelectTrigger
				size={props.size}
				variant={props.variant}
				invalid={props.invalid}
				disabled={props.disabled}
				className="w-48"
			>
				<SelectValue placeholder="Pick a fruit" />
			</SelectTrigger>
			<SelectContent>
				<SelectGroup>
					<SelectLabel>Fruits</SelectLabel>
					<SelectItem value="apple">Apple</SelectItem>
					<SelectItem value="banana">Banana</SelectItem>
					<SelectItem value="cherry">Cherry</SelectItem>
					<SelectSeparator />
					<SelectItem value="grape">Grape</SelectItem>
					<SelectItem value="mango">Mango</SelectItem>
				</SelectGroup>
			</SelectContent>
		</Select>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<BasicSelect />
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						variants x sizes
					</div>
					<div className="space-y-3">
						{VARIANTS.map((v) => (
							<div key={v} className="flex items-start gap-3">
								<div className="w-20 pt-2 font-mono text-xs text-text-muted">{v}</div>
								{SIZES.map((s) => (
									<BasicSelect key={s} size={s} variant={v} />
								))}
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						states
					</div>
					<div className="flex flex-wrap gap-3">
						<BasicSelect />
						<BasicSelect disabled />
						<BasicSelect invalid />
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Select",
};

export default meta;
