import type { Meta, StoryObj } from "@storybook/react-vite";
import { Badge } from "./badge";
import { List, ListItem } from "./list";
import { Prose } from "./prose";

const label = "mb-3 font-mono text-xs uppercase tracking-widest text-text-muted";

export const Bullet: StoryObj = {
	render: () => (
		<div className="p-8">
			<List>
				<ListItem>Planes hold cells</ListItem>
				<ListItem>Cells run Nu programs</ListItem>
				<ListItem>Programs draw ui refs</ListItem>
			</List>
		</div>
	),
};

export const Numbered: StoryObj = {
	render: () => (
		<div className="p-8">
			<List variant="number">
				<ListItem>Install the stack</ListItem>
				<ListItem>Run the demo</ListItem>
				<ListItem>Open localhost:8080</ListItem>
			</List>
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="grid max-w-3xl grid-cols-2 gap-10 p-8">
			<div>
				<div className={label}>bullet</div>
				<List>
					<ListItem>One</ListItem>
					<ListItem>Two</ListItem>
					<ListItem>Three</ListItem>
				</List>
			</div>
			<div>
				<div className={label}>number</div>
				<List variant="number">
					<ListItem>One</ListItem>
					<ListItem>Two</ListItem>
					<ListItem>Three</ListItem>
				</List>
			</div>
			<div>
				<div className={label}>number, start 7</div>
				<List variant="number" start={7}>
					<ListItem>Seven</ListItem>
					<ListItem>Eight</ListItem>
					<ListItem>Nine</ListItem>
					<ListItem>Ten</ListItem>
				</List>
			</div>
			<div>
				<div className={label}>long items wrap under their text</div>
				<List>
					<ListItem>
						A long item that runs past the measure, so the second line has to sit under the
						first line's text and not under the marker.
					</ListItem>
					<ListItem>A short one after it</ListItem>
				</List>
			</div>
			<div>
				<div className={label}>rich items</div>
				<List>
					<ListItem>
						<a className="text-accent-2 underline underline-offset-2" href="#list">
							Untitled plane
						</a>
					</ListItem>
					<ListItem>
						Worker 3{" "}
						<Badge size="sm" variant="ok">
							up
						</Badge>
					</ListItem>
					<ListItem>
						<code className="rounded-sm bg-bg-sunken px-1 py-0.5 font-mono text-sm">
							nu demo movies
						</code>
					</ListItem>
				</List>
			</div>
		</div>
	),
};

/** The same list from data and from markdown: they should be indistinguishable. */
export const SameAsProse: StoryObj = {
	render: () => (
		<div className="grid max-w-3xl grid-cols-2 gap-10 p-8">
			<div>
				<div className={label}>List</div>
				<List>
					<ListItem>markdown in, markdown out</ListItem>
					<ListItem>last actor wins, no merge</ListItem>
					<ListItem>the source is what the program sees</ListItem>
				</List>
				<div className="h-2" />
				<List variant="number">
					<ListItem>first</ListItem>
					<ListItem>second</ListItem>
				</List>
			</div>
			<div>
				<div className={label}>Prose</div>
				<Prose>
					<ul>
						<li>markdown in, markdown out</li>
						<li>last actor wins, no merge</li>
						<li>the source is what the program sees</li>
					</ul>
					<ol>
						<li>first</li>
						<li>second</li>
					</ol>
				</Prose>
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/List",
};

export default meta;
