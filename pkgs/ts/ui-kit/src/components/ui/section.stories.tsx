import type { Meta, StoryObj } from "@storybook/react-vite";
import { Button } from "./button";
import { Section } from "./section";

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-3xl">
			<Section
				title="Runs"
				description="Everything the workspace has executed in the last day."
				actions={<Button size="sm">New run</Button>}
			>
				<div className="rounded-md border border-border-subtle bg-bg-surface p-4 text-sm text-text-primary">
					Body slot.
				</div>
			</Section>
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 max-w-3xl flex flex-col gap-8 divide-y divide-border-subtle [&>*:not(:last-child)]:pb-8">
			<Section
				title="Default section"
				description="The stack that holds the sections draws the hairlines."
				actions={
					<Button size="sm" variant="secondary">
						Action
					</Button>
				}
			>
				<div className="text-sm text-text-primary">Default body.</div>
			</Section>

			<Section
				title="Second section"
				description="A hairline over it, from the stack."
				actions={
					<Button size="sm" variant="secondary">
						Action
					</Button>
				}
			>
				<div className="text-sm text-text-primary">Second body.</div>
			</Section>

			<Section size="lg" title="Roomy section" description="size=lg opens vertical breathing room.">
				<div className="text-sm text-text-primary">Roomy body.</div>
			</Section>
		</div>
	),
};

const meta: Meta = {
	title: "UI/Section",
};

export default meta;
