import type { Meta, StoryObj } from "@storybook/react-vite";
import { Markdown } from "./markdown";

// Prose is the reading surface a document sits on; the document itself is
// drawn by the prose schema, whose headings, lists and tables carry the
// element recipes (lib/recipes.ts). So the sample is real markdown through
// `Markdown` (Prose + the engine), not raw HTML, which would show only half
// the look.
const SAMPLE = `# Design system

Prose renders a document through kit tokens. This block themes on both
light and dark canvases with no extra wrapping.

## Second level

Body copy sits at \`text-lg\` with \`text-text-primary\`. Links land at
[accent-2](#) for a legible read.

### Lists

- Unordered item one
- Unordered item two
- Unordered item three

1. Ordered item one
2. Ordered item two

> The primitives are the alphabet. Compose them into your sentence, and
> don't reach for a bespoke component before you have to.

### Code

\`\`\`tsx
import { Button } from "@nustackdev/ui-kit";

<Button>Save</Button>
\`\`\`

---

Horizontal rules use **border-subtle**. Emphasized text stays *italic* and
inline styling flows naturally.
`;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-2xl">
			<Markdown value={SAMPLE} />
		</div>
	),
};

export const Matrix = Default;

const meta: Meta = {
	title: "UI/Prose",
};

export default meta;
