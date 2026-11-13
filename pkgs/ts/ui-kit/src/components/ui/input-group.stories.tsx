import type { Meta, StoryObj } from "@storybook/react-vite";
import { Send, Square } from "lucide-react";
import { Button } from "./button";
import { Field, Label } from "./field";
import { IconButton } from "./icon-button";
import { Input } from "./input";
import { SearchInput } from "./input-affix";
import { InputGroup } from "./input-group";

const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-xl">
			<InputGroup>
				<Input aria-label="Film" placeholder="A film to add" />
				<Button>Add film</Button>
			</InputGroup>
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 max-w-xl space-y-6">
			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					sizes
				</div>
				<div className="space-y-3">
					{SIZES.map((s) => (
						<InputGroup key={s}>
							<Input size={s} aria-label={`Name ${s}`} placeholder={`Size ${s}`} />
							<Button size={s}>Create</Button>
						</InputGroup>
					))}
				</div>
			</div>

			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					shapes
				</div>
				<div className="space-y-4">
					<InputGroup>
						<div className="flex flex-col gap-1">
							<Label htmlFor="group-job">New job</Label>
							<Input id="group-job" placeholder="Job name" />
						</div>
						<Button>Create job</Button>
					</InputGroup>
					<InputGroup>
						<Input aria-label="Say" placeholder="Say something" />
						<Button>
							<Send />
							Say
						</Button>
						<Button variant="secondary">
							<Square />
							Stop
						</Button>
					</InputGroup>
					<InputGroup>
						<SearchInput aria-label="Search" value="" onClear={() => {}} placeholder="Search" />
						<IconButton aria-label="Send" variant="secondary">
							<Send />
						</IconButton>
					</InputGroup>
					<Field
						id="group-title"
						label="Title"
						help="Help sits under the whole group"
						error="Taken"
					>
						<InputGroup>
							<Input
								id="group-title"
								aria-describedby="group-title-help group-title-error"
								invalid
								placeholder="Title"
							/>
							<Button>Save</Button>
						</InputGroup>
					</Field>
					<InputGroup>
						<Input disabled aria-label="Disabled" placeholder="Disabled" />
						<Button disabled>Go</Button>
					</InputGroup>
				</div>
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/InputGroup",
};

export default meta;
