import type { Meta, StoryObj } from "@storybook/react-vite";
import { Html } from "./html";

const STYLE =
	"<style>body{margin:0;padding:20px;font:14px/1.5 system-ui,sans-serif;background:#15181f;color:#eceef4}</style>";

const CARD = `${STYLE}<h3 style="margin:0 0 8px">A whole document</h3>
<p style="margin:0;color:#bcc1cc">Its own head, styles and scripts. The frame takes its height from the content.</p>`;

// Adds a line every second for ten seconds: the frame follows.
const GROWING = `${STYLE}<div id="log"></div><script>
let n = 0;
const t = setInterval(() => {
	const p = document.createElement("p");
	p.style.margin = "0 0 6px";
	p.textContent = "line " + ++n;
	document.getElementById("log").append(p);
	if (n === 10) clearInterval(t);
}, 1000);
</script>`;

const LONG = `${STYLE}${Array.from({ length: 30 }, (_, i) => `<p style="margin:0 0 6px">row ${i + 1}</p>`).join("")}`;

// Scripts run, but the frame is its own origin: the page around it is out of reach.
const SANDBOX = `${STYLE}<pre id="out" style="margin:0"></pre><script>
const out = document.getElementById("out");
const tryIt = (label, fn) => { try { fn(); out.textContent += label + ": allowed\\n"; } catch (e) { out.textContent += label + ": blocked\\n"; } };
tryIt("scripts", () => {});
tryIt("parent.document", () => parent.document.title);
tryIt("localStorage", () => localStorage.length);
tryIt("cookies", () => document.cookie);
</script>`;

const label = "mb-2 font-mono text-xs uppercase tracking-widest text-text-muted";

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-2xl">
			<Html html={CARD} title="A whole document" />
		</div>
	),
};

export const Growing: StoryObj = {
	render: () => (
		<div className="p-8 max-w-2xl">
			<Html html={GROWING} title="Growing content" />
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 max-w-2xl space-y-6">
			<div>
				<div className={label}>auto height</div>
				<Html html={LONG} title="Auto height" />
			</div>
			<div>
				<div className={label}>fixed height, scrolls inside</div>
				<Html html={LONG} title="Fixed height" height={160} />
			</div>
			<div>
				<div className={label}>no border</div>
				<Html html={CARD} title="No border" bordered={false} />
			</div>
			<div>
				<div className={label}>radius</div>
				<div className="grid grid-cols-4 gap-3">
					{(["none", "sm", "md", "lg"] as const).map((r) => (
						<Html key={r} html={CARD} title={`radius ${r}`} radius={r} />
					))}
				</div>
			</div>
		</div>
	),
};

export const Sandbox: StoryObj = {
	render: () => (
		<div className="p-8 max-w-2xl">
			<Html html={SANDBOX} title="Sandbox" />
		</div>
	),
};

const meta: Meta = {
	title: "UI/Html",
};

export default meta;
