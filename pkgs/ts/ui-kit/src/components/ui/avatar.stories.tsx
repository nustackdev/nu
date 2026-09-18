import type { Meta, StoryObj } from "@storybook/react-vite";
import { Avatar, AvatarFallback, AvatarImage } from "./avatar";

const SIZES = ["sm", "md", "lg", "xl"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<Avatar>
					<AvatarImage src="https://avatars.githubusercontent.com/u/1?v=4" alt="octocat" />
					<AvatarFallback>OC</AvatarFallback>
				</Avatar>
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
					<div className="flex items-end gap-4">
						{SIZES.map((s) => (
							<div key={s} className="flex flex-col items-center gap-2">
								<Avatar size={s}>
									<AvatarFallback>GM</AvatarFallback>
								</Avatar>
								<div className="font-mono text-xs text-text-muted">{s}</div>
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						fallback vs image
					</div>
					<div className="flex items-center gap-3">
						<Avatar>
							<AvatarFallback>GM</AvatarFallback>
						</Avatar>
						<Avatar>
							<AvatarFallback>AB</AvatarFallback>
						</Avatar>
						<Avatar>
							<AvatarImage src="/does-not-exist.png" alt="broken" />
							<AvatarFallback>CD</AvatarFallback>
						</Avatar>
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Avatar",
};

export default meta;
