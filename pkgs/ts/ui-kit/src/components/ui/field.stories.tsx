import type { Meta, StoryObj } from "@storybook/react-vite";
import { Checkbox } from "./checkbox";
import { Field, FieldError, FieldHelp, Label, useFieldControl } from "./field";
import { Input } from "./input";
import { TextArea } from "./text-area";

// A control that reads the Field it sits in: id, describedby, invalid,
// required and disabled land on the real element.
function FieldInput(props: React.ComponentProps<typeof Input>) {
	const f = useFieldControl();
	return (
		<Input
			id={f?.id}
			aria-describedby={f?.describedBy}
			invalid={f?.invalid}
			required={f?.required}
			disabled={f?.disabled}
			{...props}
		/>
	);
}

function FieldTextArea(props: React.ComponentProps<typeof TextArea>) {
	const f = useFieldControl();
	return (
		<TextArea
			id={f?.id}
			aria-describedby={f?.describedBy}
			invalid={f?.invalid}
			required={f?.required}
			disabled={f?.disabled}
			{...props}
		/>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-sm">
			<Field label="Title" help="As released">
				<FieldInput placeholder="e.g. Arrival" />
			</Field>
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 max-w-sm space-y-6">
			<Field label="Plain">
				<FieldInput placeholder="Nothing else" />
			</Field>
			<Field label="With help" help="Help sits under the control">
				<FieldInput placeholder="Type here" />
			</Field>
			<Field label="Required" required help="The asterisk is a hint, `required` is on the input">
				<FieldInput placeholder="Needed" />
			</Field>
			<Field label="Invalid" help="Help stays when the error shows" error="That will not do">
				<FieldInput defaultValue="wrong" />
			</Field>
			<Field label="Disabled" disabled help="The label dims with the control">
				<FieldInput defaultValue="locked" />
			</Field>
			<Field label="Notes" error="Too short">
				<FieldTextArea rows={2} defaultValue="ok" />
			</Field>
		</div>
	),
};

export const Parts: StoryObj = {
	render: () => (
		<div className="p-8 max-w-sm space-y-4">
			<div className="flex flex-col gap-1">
				<Label htmlFor="parts-name" required>
					Name
				</Label>
				<Input id="parts-name" aria-describedby="parts-help parts-error" invalid required />
				<FieldHelp id="parts-help">Label, FieldHelp and FieldError on their own</FieldHelp>
				<FieldError id="parts-error">Needs a name</FieldError>
			</div>
			<div className="flex items-center gap-2">
				<Checkbox id="parts-check" />
				<Label htmlFor="parts-check" inline>
					An inline label, beside a checkbox
				</Label>
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/Field",
};

export default meta;
