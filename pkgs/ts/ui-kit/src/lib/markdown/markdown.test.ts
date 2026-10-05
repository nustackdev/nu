// Round-trip tests.
//
// The contract the Ref's value rests on: markdown in, the same markdown out.
// Anything the editor can produce has to survive a lap through the document
// model unchanged, or a MarkdownRef churns on every touch.
//
// Two properties are tested separately because they are different claims:
//
//   stable(md)  - md -> doc -> md is the identity. This is the one that
//                 matters for churn, and it must hold for everything the
//                 serializer itself emits.
//   settles(md) - one lap normalizes (source hard-wrapping reflows), and
//                 every lap after that is the identity. This is the honest
//                 claim for hand-written markdown that was not written by us.
//
// Run: npm test -w @nustackdev/ui-kit

import { describe, expect, it } from "vitest";
import { createMarkdown, parseMarkdown, posForOffset, serializeMarkdown } from "./markdown";
import { createProseSchema, proseSchema, safeUrl } from "./schema";

function lap(md: string): string {
	return serializeMarkdown(parseMarkdown(md).doc);
}

/** md -> doc -> md is the identity. */
function stable(md: string): void {
	expect(lap(md)).toBe(md);
}

/** One lap normalizes; every lap after that is the identity. */
function settles(md: string): string {
	const once = lap(md);
	expect(lap(once)).toBe(once);
	return once;
}

describe("blocks round-trip", () => {
	it("keeps paragraphs", () => stable("hello world\n"));

	it("keeps blank-line separated paragraphs", () => stable("first para\n\nsecond para\n"));

	it("keeps all six heading levels", () =>
		stable("# one\n\n## two\n\n### three\n\n#### four\n\n##### five\n\n###### six\n"));

	it("keeps bullet lists", () => stable("- a\n- b\n- c\n"));

	it("keeps numbered lists", () => stable("1. a\n2. b\n3. c\n"));

	it("keeps a numbered list that does not start at one", () => stable("3. a\n4. b\n"));

	it("keeps blockquotes", () => stable("> quoted line\n"));

	it("keeps multi-paragraph blockquotes", () => stable("> one\n>\n> two\n"));

	it("keeps rules", () => stable("before\n\n---\n\nafter\n"));

	it("keeps nested lists", () => stable("- a\n  - b\n  - c\n- d\n"));

	it("keeps a list mixed with a heading", () => stable("# title\n\n- a\n- b\n\nbody\n"));

	it("keeps checklists", () => stable("- [ ] todo\n- [x] done\n"));

	it("keeps a nested checklist", () => stable("- [ ] a\n  - [x] b\n- [ ] c\n"));

	it("keeps an empty checklist item", () => stable("- [ ] \n"));

	it("keeps a code fence", () => stable("```python\ndef f():\n    return 1\n```\n"));

	it("keeps a code fence with no language", () => stable("```\nplain\n```\n"));

	it("keeps an empty code fence", () => stable("```\n```\n"));

	it("keeps blank lines and markup inside a fence literally", () =>
		stable("```md\n# not a heading\n\n- not a list **x**\n```\n"));

	it("keeps a fence between paragraphs", () => stable("before\n\n```sh\nls -la\n```\n\nafter\n"));

	it("keeps a fence inside a list item", () =>
		stable("- run this\n\n  ```sh\n  ls\n  ```\n- done\n"));

	it("outgrows backticks inside the fence", () => {
		const doc = parseMarkdown("````\n```\ninner\n```\n````\n").doc;
		expect(doc.firstChild?.type.name).toBe("code_block");
		expect(doc.textContent).toBe("```\ninner\n```");
		stable(serializeMarkdown(doc));
	});

	it("reads a tilde fence and normalizes it to backticks", () => {
		const doc = parseMarkdown("~~~js\nx\n~~~\n").doc;
		expect(doc.firstChild?.attrs.language).toBe("js");
		expect(settles("~~~js\nx\n~~~\n")).toBe("```js\nx\n```\n");
	});

	it("runs an unclosed fence to the end", () => {
		const doc = parseMarkdown("```\na\n\nb\n").doc;
		expect(doc.childCount).toBe(1);
		expect(doc.textContent).toBe("a\n\nb");
	});

	it("reads checklist state and kind", () => {
		const list = parseMarkdown("- [ ] a\n- [X] b\n").doc.firstChild;
		expect(list?.type.name).toBe("task_list");
		expect(list?.child(0).attrs.checked).toBe(false);
		expect(list?.child(1).attrs.checked).toBe(true);
	});

	it("splits a bullet list from a checklist", () => {
		const doc = parseMarkdown("- a\n- [ ] b\n- c\n").doc;
		expect(doc.content.content.map((n) => n.type.name)).toEqual([
			"bullet_list",
			"task_list",
			"bullet_list",
		]);
	});

	it("empty source is empty", () => {
		expect(lap("")).toBe("");
		expect(parseMarkdown("").doc.childCount).toBe(1);
	});
});

describe("marks round-trip", () => {
	it("keeps bold", () => stable("a **bold** b\n"));
	it("keeps italic", () => stable("a *slanted* b\n"));
	it("keeps code", () => stable("a `code()` b\n"));
	it("keeps links", () => stable("see [docs](https://nustack.dev) now\n"));
	it("keeps nested marks", () => stable("a **bold *and* more** b\n"));
	it("keeps a link around a mark", () => stable("[**bold link**](https://x.dev)\n"));
	it("keeps marks inside a list item", () => stable("- `/` opens the menu\n"));
	it("keeps marks inside a heading", () => stable("# a **loud** title\n"));
	it("keeps images", () => stable("look ![a cat](https://x.dev/cat.png) here\n"));
	it("keeps an image inside a link", () => stable("[![logo](logo.svg)](https://x.dev)\n"));
	it("keeps an image with no alt text", () => stable("![](a.png)\n"));

	it("reads an image as a node, not as text", () => {
		const p = parseMarkdown("![a \\] b](x.png)\n").doc.firstChild;
		expect(p?.firstChild?.type.name).toBe("image");
		expect(p?.firstChild?.attrs.alt).toBe("a ] b");
		stable(serializeMarkdown(parseMarkdown("![a \\] b](x.png)\n").doc));
	});
});

describe("escaping", () => {
	it("escapes what would otherwise re-parse as a mark", () => {
		const md = lap("a *not emphasis b\n");
		expect(lap(md)).toBe(md);
		expect(parseMarkdown(md).doc.textContent).toBe("a *not emphasis b");
	});

	it("round-trips text that looks like markup", () => {
		const source = "2 * 3 * 4 and _under_ and `tick` and [link](x)";
		// serialize the *document* whose text is that literal string
		const doc = parseMarkdown(source.replace(/([*_`[\]])/g, "\\$1")).doc;
		expect(doc.textContent).toBe(source);
		const md = serializeMarkdown(doc);
		expect(parseMarkdown(md).doc.textContent).toBe(source);
		stable(md);
	});

	it("escapes a leading block marker in body text", () => {
		const doc = parseMarkdown("\\# not a heading\n").doc;
		expect(doc.firstChild?.type.name).toBe("paragraph");
		expect(doc.textContent).toBe("# not a heading");
		stable(serializeMarkdown(doc));
	});

	it("escapes a list item that only looks like a checkbox", () => {
		const doc = parseMarkdown("- \\[ ] literal\n").doc;
		expect(doc.firstChild?.type.name).toBe("bullet_list");
		expect(doc.textContent).toBe("[ ] literal");
		stable(serializeMarkdown(doc));
	});

	it("escapes a paragraph that would open a fence", () => {
		const doc = parseMarkdown("\\```not a fence\n").doc;
		expect(doc.firstChild?.type.name).toBe("paragraph");
		stable(serializeMarkdown(doc));
	});

	it("escapes text that would read back as an image", () => {
		const doc = parseMarkdown("\\!\\[x](y)\n").doc;
		expect(doc.textContent).toBe("![x](y)");
		stable(serializeMarkdown(doc));
	});

	it("escapes a bare backslash", () => {
		const doc = parseMarkdown("back\\\\slash\n").doc;
		expect(doc.textContent).toBe("back\\slash");
		stable(serializeMarkdown(doc));
	});
});

describe("tables", () => {
	const { schema, nodeType } = proseSchema;

	/** The table's cells as text, row by row. */
	function grid(md: string): string[][] {
		const table = parseMarkdown(md).doc.firstChild;
		expect(table?.type.name).toBe("table");
		const rows: string[][] = [];
		table?.forEach((row) => {
			const cells: string[] = [];
			row.forEach((cell) => {
				cells.push(cell.textContent);
			});
			rows.push(cells);
		});
		return rows;
	}

	function aligns(md: string): (string | null)[] {
		const out: (string | null)[] = [];
		parseMarkdown(md).doc.firstChild?.firstChild?.forEach((cell) => {
			out.push(cell.attrs.align);
		});
		return out;
	}

	/** A one-cell table whose cell holds `inline`, as the editor would build it. */
	function cellDoc(...inline: ReturnType<typeof schema.text>[]) {
		const p = nodeType.paragraph.create(null, inline);
		const row = nodeType.tableRow.create(null, [nodeType.tableHeader.create(null, p)]);
		return schema.topNodeType.create(null, [nodeType.table.create(null, [row])]);
	}

	it("keeps a table", () => stable("| a | b |\n| --- | --- |\n| 1 | 2 |\n| 3 | 4 |\n"));

	it("keeps a header-only table", () => stable("| a | b |\n| --- | --- |\n"));

	it("keeps a one-column table", () => stable("| a |\n| --- |\n| 1 |\n"));

	it("keeps every alignment", () => {
		const md = "| n | l | c | r |\n| --- | :--- | :---: | ---: |\n| 1 | 2 | 3 | 4 |\n";
		stable(md);
		expect(aligns(md)).toEqual([null, "left", "center", "right"]);
		// every cell of a column carries the column's alignment
		const body = parseMarkdown(md).doc.firstChild?.child(1);
		expect(body?.child(3).attrs.align).toBe("right");
	});

	it("reads the header as header cells and the rest as body cells", () => {
		const table = parseMarkdown("| a |\n| --- |\n| 1 |\n").doc.firstChild;
		expect(table?.child(0).firstChild?.type.name).toBe("table_header");
		expect(table?.child(1).firstChild?.type.name).toBe("table_cell");
		expect(table?.child(1).firstChild?.firstChild?.type.name).toBe("paragraph");
	});

	it("keeps empty cells", () => {
		stable("| a |  | c |\n| --- | --- | --- |\n|  | 2 |  |\n");
		expect(grid("| a |  | c |\n| --- | --- | --- |\n|  | 2 |  |\n")).toEqual([
			["a", "", "c"],
			["", "2", ""],
		]);
	});

	it("keeps an all-empty table", () => stable("|  |  |\n| --- | --- |\n|  |  |\n"));

	it("keeps marks, code, links and images in cells", () =>
		stable(
			"| **bold** | *em* | `code` | [link](https://x.dev) | ![alt](a.png) |\n" +
				"| --- | --- | --- | --- | --- |\n" +
				"| a **b *c*** | `x()` y | [**l**](u) | [![i](i.png)](u) | \\*lit* |\n",
		));

	it("keeps a table between other blocks", () =>
		stable("# t\n\nintro\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n\nafter\n"));

	it("keeps two tables in a row", () => stable("| a |\n| --- |\n| 1 |\n\n| b |\n| --- |\n| 2 |\n"));

	it("keeps a table in a quote and in a list item", () => {
		stable("> | a | b |\n> | --- | --- |\n> | 1 | 2 |\n");
		stable("- item\n\n  | a | b |\n  | --- | --- |\n  | 1 | 2 |\n- next\n");
		stable("- item\n\n  | a |\n  | --- |\n  - nested\n");
	});

	describe("pipes in cells", () => {
		it("reads an escaped pipe as a pipe, not a boundary", () => {
			expect(grid("| a \\| b | c |\n| --- | --- |\n")).toEqual([["a | b", "c"]]);
			stable("| a \\| b | c |\n| --- | --- |\n");
		});

		it("reads an escaped pipe inside code as a pipe", () => {
			const md = "| `a \\| b` |\n| --- |\n";
			const cell = parseMarkdown(md).doc.firstChild?.firstChild?.firstChild;
			expect(cell?.textContent).toBe("a | b");
			expect(cell?.firstChild?.firstChild?.marks.map((m) => m.type.name)).toEqual(["code"]);
			stable(md);
		});

		it("writes every pipe a cell holds escaped, code included", () => {
			const text = cellDoc(
				schema.text("x|y "),
				schema.text("a|b", [proseSchema.markType.code.create()]),
			);
			const md = serializeMarkdown(text);
			expect(md).toBe("| x\\|y `a\\|b` |\n| --- |\n");
			expect(parseMarkdown(md).doc.textContent).toBe("x|y a|b");
			stable(md);
		});

		it("keeps backslashes next to pipes apart from the escape", () => {
			for (const t of ["a\\", "a\\|b", "\\|", "|\\", "\\\\|", "a | \\ | b"]) {
				const md = serializeMarkdown(cellDoc(schema.text(t)));
				expect(parseMarkdown(md).doc.textContent).toBe(t);
				stable(md);
			}
			const code = proseSchema.markType.code.create();
			// (Code ending in a backslash is out of reach anywhere, cell or not.)
			for (const t of ["a\\|b", "|", "a|\\b", "\\|"]) {
				const md = serializeMarkdown(cellDoc(schema.text(t, [code])));
				expect(parseMarkdown(md).doc.textContent).toBe(t);
				stable(md);
			}
		});

		it("keeps a pipe in a link, an image and its alt", () => {
			const md = "| [a\\|b](x?q=1\\|2) | ![p\\|q](i\\|.png) |\n| --- | --- |\n";
			const p = parseMarkdown(md).doc.firstChild?.firstChild;
			expect(p?.child(0).firstChild?.firstChild?.marks[0].attrs.href).toBe("x?q=1|2");
			expect(p?.child(1).firstChild?.firstChild?.attrs.alt).toBe("p|q");
			expect(p?.child(1).firstChild?.firstChild?.attrs.src).toBe("i|.png");
			stable(md);
		});
	});

	describe("cells are not blocks", () => {
		it("does not block-escape what would open a block on a line of its own", () => {
			const md =
				"| - a | # b | > c | 1. d | --- | ``` | [ ] e |\n" +
				"| --- | --- | --- | --- | --- | --- | --- |\n";
			stable(md);
			expect(grid(md)).toEqual([["- a", "# b", "> c", "1. d", "---", "```", "[ ] e"]]);
		});

		it("still escapes marks in a cell", () => {
			const md = serializeMarkdown(cellDoc(schema.text("2 * 3 * 4")));
			expect(md).toBe("| 2 \\* 3 * 4 |\n| --- |\n");
			stable(md);
		});

		it("settles a hand-escaped block marker in a cell", () =>
			expect(settles("| \\- a |\n| --- |\n")).toBe("| - a |\n| --- |\n"));

		it("drops edge whitespace in a cell, which only reads back as padding", () => {
			const md = serializeMarkdown(cellDoc(schema.text("  a b  ")));
			expect(md).toBe("| a b |\n| --- |\n");
			stable(md);
		});
	});

	describe("hand-written tables settle into the one form", () => {
		const cases: [string, string][] = [
			["no outer pipes", "a | b\n--- | ---\n1 | 2\n"],
			["leading pipes only", "| a | b\n| --- | ---\n| 1 | 2\n"],
			["trailing pipes only", "a | b |\n--- | --- |\n1 | 2 |\n"],
			["ragged widths", "| a   | b |\n|-----|:-:|\n| 1 |    2     |\n"],
			["tight pipes", "|a|b|\n|-|-|\n|1|2|\n"],
			["extra spaces and dashes", "|   a   |   b   |\n|  ------  |  ------:  |\n|  1  |  2  |\n"],
		];
		for (const [name, md] of cases) {
			it(name, () => {
				const once = settles(md);
				expect(once).toMatch(/^\| a \| b \|\n\| --- \| (---|:---:|---:) \|\n\| 1 \| 2 \|\n$/);
			});
		}

		it("pads a short row with empty cells", () =>
			expect(settles("| a | b | c |\n| --- | --- | --- |\n| 1 |\n")).toBe(
				"| a | b | c |\n| --- | --- | --- |\n| 1 |  |  |\n",
			));

		it("drops the extra cells of a long row", () =>
			expect(settles("| a |\n| --- |\n| 1 | 2 | 3 |\n")).toBe("| a |\n| --- |\n| 1 |\n"));

		it("takes a line with no pipe as a one-cell row", () =>
			expect(settles("| a | b |\n| --- | --- |\nfoo\n")).toBe(
				"| a | b |\n| --- | --- |\n| foo |  |\n",
			));

		it("ends at a blank line or the next block", () => {
			const doc = parseMarkdown("| a |\n| --- |\n| 1 |\n- list\n\n| b |\n| --- |\n# h\n").doc;
			expect(doc.content.content.map((n) => n.type.name)).toEqual([
				"table",
				"bullet_list",
				"table",
				"heading",
			]);
		});

		it("starts a table under a hard-wrapped paragraph line", () => {
			const doc = parseMarkdown("intro\nline\n| a |\n| --- |\n").doc;
			expect(doc.content.content.map((n) => n.type.name)).toEqual(["paragraph", "table"]);
			expect(doc.firstChild?.textContent).toBe("intro line");
		});

		it("reads a table in a list item's continuation", () => {
			const doc = parseMarkdown("- item\n  | a |\n  | --- |\n").doc;
			expect(doc.firstChild?.firstChild?.child(1).type.name).toBe("table");
		});
	});

	describe("what is not a table", () => {
		const prose = (md: string, names: string[]) => {
			const doc = parseMarkdown(md).doc;
			expect(doc.content.content.map((n) => n.type.name)).toEqual(names);
			stable(serializeMarkdown(doc));
		};

		it("a lone pipe line", () => prose("| a | b |\n", ["paragraph"]));

		it("a header and delimiter with different counts", () =>
			prose("| a | b |\n| --- |\n", ["paragraph"]));

		it("a delimiter line with no pipe", () => {
			// `---` under a line is a rule here, not a one-column table
			const doc = parseMarkdown("| a |\n---\n").doc;
			expect(doc.content.content.map((n) => n.type.name)).toEqual(["paragraph", "horizontal_rule"]);
		});

		it("a header line with no pipe", () => prose("a\n-|-\n", ["paragraph"]));

		it("a delimiter cell that is not dashes", () =>
			prose("| a | b |\n| --- | x |\n", ["paragraph"]));

		it("a delimiter row that is a list item", () => {
			const doc = parseMarkdown("a | b\n- | -\n").doc;
			expect(doc.content.content.map((n) => n.type.name)).toEqual(["paragraph", "bullet_list"]);
		});

		it("an escaped pipe is no header", () => prose("a \\| b\n--- | ---\n", ["paragraph"]));

		it("pipes in a paragraph, then a delimiter-looking paragraph", () => {
			// Two paragraphs: the serializer never puts them on adjacent lines.
			const doc = schema.topNodeType.create(null, [
				nodeType.paragraph.create(null, schema.text("| a | b |")),
				nodeType.paragraph.create(null, schema.text("| --- | --- |")),
			]);
			const md = serializeMarkdown(doc);
			expect(md).toBe("| a | b |\n\n| --- | --- |\n");
			expect(parseMarkdown(md).doc.childCount).toBe(2);
			stable(md);
		});

		it("a list item with pipes over a nested item that looks like a delimiter", () => {
			for (const nested of ["| --- |", "--- | ---", ":-: | -"]) {
				const item = nodeType.listItem.create(null, [
					nodeType.paragraph.create(null, schema.text("| a |")),
					nodeType.bulletList.create(null, [
						nodeType.listItem.create(null, nodeType.paragraph.create(null, schema.text(nested))),
					]),
				]);
				const doc = schema.topNodeType.create(null, [nodeType.bulletList.create(null, [item])]);
				const md = serializeMarkdown(doc);
				expect(parseMarkdown(md).doc.eq(doc)).toBe(true);
				stable(md);
			}
		});

		it("list items that look like a header and a delimiter", () =>
			prose("- | a | b |\n- | --- | --- |\n", ["bullet_list"]));
	});

	it("maps a cell's source offset to its text", () => {
		const md = "| ab | cd |\n| --- | --- |\n| ef | g\\|h |\n";
		const parsed = parseMarkdown(md);
		const at = md.indexOf("g\\|h") + 4; // after `g\|h`
		const pos = posForOffset(parsed, at);
		expect(parsed.doc.resolve(pos).parent.textContent).toBe("g|h");
	});

	it("writes a spanning cell as itself plus empty cells", () => {
		const cell = (t: string, attrs = {}) =>
			nodeType.tableCell.create(attrs, nodeType.paragraph.create(null, t ? schema.text(t) : null));
		const head = (t: string) =>
			nodeType.tableHeader.create(null, nodeType.paragraph.create(null, schema.text(t)));
		const doc = schema.topNodeType.create(null, [
			nodeType.table.create(null, [
				nodeType.tableRow.create(null, [head("a"), head("b"), head("c")]),
				nodeType.tableRow.create(null, [cell("wide", { colspan: 2 }), cell("x")]),
			]),
		]);
		const md = serializeMarkdown(doc);
		expect(md).toBe("| a | b | c |\n| --- | --- | --- |\n| wide |  | x |\n");
		stable(md);
	});

	it("takes a column's alignment from the first cell that sets it", () => {
		const cell = (t: string, align: string | null) =>
			nodeType.tableCell.create({ align }, nodeType.paragraph.create(null, schema.text(t)));
		const doc = schema.topNodeType.create(null, [
			nodeType.table.create(null, [
				nodeType.tableRow.create(null, [
					nodeType.tableHeader.create(null, nodeType.paragraph.create(null, schema.text("h"))),
				]),
				nodeType.tableRow.create(null, [cell("1", "center")]),
				nodeType.tableRow.create(null, [cell("2", null)]),
			]),
		]);
		expect(serializeMarkdown(doc)).toBe("| h |\n| :---: |\n| 1 |\n| 2 |\n");
	});

	it("refuses an alignment markdown cannot write", () => {
		const cell = nodeType.tableCell.create({ align: "justify" }, nodeType.paragraph.create());
		expect(() => cell.check()).toThrow();
	});

	it("puts alignment on the cell's DOM and reads it back", () => {
		const cell = nodeType.tableCell.create({ align: "right" }, nodeType.paragraph.create());
		const out = cell.type.spec.toDOM?.(cell) as [string, Record<string, string>];
		expect(out[0]).toBe("td");
		expect(out[1]).toEqual({ style: "text-align: right" });
		const plain = nodeType.tableHeader.create(null, nodeType.paragraph.create());
		const bare = plain.type.spec.toDOM?.(plain) as [string, object];
		expect(bare[1]).toEqual({});
	});
});

describe("normalization settles after one lap", () => {
	// Hand-written markdown, hard-wrapped the way a person writes it.
	const WRAPPED = `# Pages

This is a **prose document**. One Ref, many paragraphs. Type freely, select
across paragraphs, retype a range -- inside one it behaves like a text
editor, because it is one.

The value never stops being markdown. What the server wrote is what comes
back, minus the source wrapping.

- \`# \` at the start of a line makes a heading
- \`- \` starts a list
- \`cmd+b\` bolds *the selection*
`;

	it("reflows hard wrapping once, then holds", () => {
		const once = settles(WRAPPED);
		expect(once).toContain("# Pages\n");
		expect(once).toContain("**prose document**");
		expect(once).toContain("- `# ` at the start of a line");
		// the wrap is gone, the content is not
		expect(once).not.toContain("select\nacross paragraphs");
		expect(parseMarkdown(once).doc.textContent).toContain("across paragraphs, retype a range");
	});

	it("holds for every shape a seeded document takes", () => {
		const blocks = [
			WRAPPED,
			"A program block is a python module with an `out` entry\npoint that returns a Nu term.\n",
			"The block below names a ref whose *path* is itself read from\na ref.\n",
			"Every block above is a live Nu program in its own supervised\nsection.\n",
		];
		for (const md of blocks) settles(md);
	});
});

describe("a fence language the parser cannot read is never written", () => {
	const { schema, nodeType } = proseSchema;

	/** A document of: a fence with `language`, a paragraph, a second fence. */
	function fenced(language: string) {
		return schema.topNodeType.create(null, [
			nodeType.codeBlock.create({ language }, schema.text("x = 1")),
			nodeType.paragraph.create(null, schema.text("between")),
			nodeType.codeBlock.create({ language: "sql" }, schema.text("select 1;")),
		]);
	}

	for (const language of ["my lang", "py`thon", "\tts ", "```"]) {
		it(`drops what a fence line cannot hold: ${JSON.stringify(language)}`, () => {
			const md = serializeMarkdown(fenced(language));
			const doc = parseMarkdown(md).doc;
			// still three blocks: the fence did not turn into text and eat the rest
			expect(doc.childCount).toBe(3);
			expect(doc.child(0).type.name).toBe("code_block");
			expect(doc.child(0).textContent).toBe("x = 1");
			expect(doc.child(1).textContent).toBe("between");
			expect(doc.child(2).type.name).toBe("code_block");
			expect(doc.child(2).attrs.language).toBe("sql");
			expect(doc.child(2).textContent).toBe("select 1;");
			settles(md);
		});
	}

	it("keeps a language with no space or backtick verbatim", () => {
		const md = serializeMarkdown(fenced("c++"));
		expect(md.startsWith("```c++\n")).toBe(true);
		stable(md);
	});
});

describe("source offsets", () => {
	it("maps a source offset to the matching document position", () => {
		const head = "one two";
		const parsed = parseMarkdown(`${head}\n\nthree\n`);
		const pos = posForOffset(parsed, head.length);
		// the caret lands at the end of the first paragraph's text
		expect(parsed.doc.textBetween(1, pos)).toBe("one two");
	});
});

describe("schema parameterisation", () => {
	// The factory exists so a downstream package can restyle `toDOM` without
	// forking the parser. Restyling must not change what markdown means.
	const styled = createMarkdown(
		createProseSchema({
			paragraph: "my-2",
			heading: (level) => `h-${level}`,
			strong: "font-semibold",
		}),
	);

	it("round-trips identically under a restyled schema", () => {
		const md = "# one\n\na **bold** para\n\n- a\n- b\n";
		expect(styled.serializeMarkdown(styled.parseMarkdown(md).doc)).toBe(md);
	});

	it("puts the recipes on toDOM and nowhere else", () => {
		const doc = styled.parseMarkdown("## two\n").doc;
		const out = doc.firstChild?.type.spec.toDOM?.(doc.firstChild) as [string, { class: string }];
		expect(out[0]).toBe("h2");
		expect(out[1].class).toBe("h-2");
	});

	it("ships no class attribute when there is no recipe", () => {
		const doc = parseMarkdown("## two\n").doc;
		const out = doc.firstChild?.type.spec.toDOM?.(doc.firstChild) as [string, object];
		expect(out[1]).toEqual({});
	});
});

describe("urls", () => {
	it("passes web, mail and relative urls", () => {
		for (const u of ["https://x.dev", "http://x.dev", "mailto:a@b.c", "/a", "a.png", "#top"]) {
			expect(safeUrl(u)).toBe(u);
		}
	});

	it("drops script and data urls", () => {
		const bad = ["javascript:alert(1)", " JavaScript:alert(1)", "data:text/html,x", "vbscript:x"];
		for (const u of bad) {
			expect(safeUrl(u)).toBe("");
		}
	});
});
