import type { Meta, StoryObj } from "@storybook/react-vite";
import { Prose } from "./prose";

const SAMPLE = (
	<>
		<h1>Design system</h1>
		<p>
			Prose renders arbitrary HTML through kit tokens. This block themes on both
			light and dark canvases with no extra wrapping.
		</p>
		<h2>Second level</h2>
		<p>
			Body copy sits at <code>text-base</code> with{" "}
			<code>text-text-primary</code>. Links land at{" "}
			<a href="#">accent-2</a> for a legible read.
		</p>
		<h3>Lists</h3>
		<ul>
			<li>Unordered item one</li>
			<li>Unordered item two</li>
			<li>Unordered item three</li>
		</ul>
		<ol>
			<li>Ordered item one</li>
			<li>Ordered item two</li>
		</ol>
		<blockquote>
			The primitives are the alphabet. Compose them into your sentence, and
			don't reach for a bespoke component before you have to.
		</blockquote>
		<h3>Code</h3>
		<pre>
			<code>{`import { Button } from "@nustackdev/ui-kit";

<Button>Save</Button>`}</code>
		</pre>
		<hr />
		<p>
			Horizontal rules use <strong>border-subtle</strong>. Emphasized text stays
			<em> italic </em>and inline styling flows naturally.
		</p>
	</>
);

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-2xl">
				<Prose>{SAMPLE}</Prose>
			</div>
	),
};

export const Matrix = Default;

const meta: Meta = {
	title: "UI/Prose",
};

export default meta;
