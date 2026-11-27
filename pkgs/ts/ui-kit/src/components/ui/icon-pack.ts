// The kit's icon pack: the lucide names the icon picker offers, in groups.
//
// What is offered, not what draws: `iconFor` (lib/icons.ts) draws any lucide
// name, so a stored value can name an icon the pack leaves out and it still
// shows. The pack is the picker's short list, sorted into groups a person can
// scan. A caller can hand the picker a pack of its own in the same shape.
//
// Names are lucide's own kebab names. The second item of an entry is extra
// words the picker's search matches on, beyond the name and the group.

/** One icon the picker offers: lucide's kebab name, then extra search words. */
export type IconPackEntry = readonly [name: string, keywords?: string];

/** A named group of the pack, shown under its label in the picker. */
export type IconPackGroup = { label: string; icons: readonly IconPackEntry[] };

/** The pack the picker offers when the caller names none, in the order it shows them. */
export const ICON_PACK: readonly IconPackGroup[] = [
	{
		label: "Files",
		icons: [
			["file-text", "document page note"],
			["type", "text font prose writing"],
			["file", "document blank"],
			["folder", "directory"],
			["folder-open", "directory"],
			["notebook-pen", "journal notes write"],
			["book-open", "read docs guide"],
			["book", "read"],
			["library", "books shelf"],
			["archive", "box old"],
			["inbox", "mail tray"],
			["clipboard", "paste"],
			["sticky-note", "memo"],
			["bookmark", "save"],
			["paperclip", "attach"],
			["newspaper", "news article"],
		],
	},
	{
		label: "Work",
		icons: [
			["briefcase", "job work"],
			["list", "items"],
			["list-todo", "tasks todo"],
			["list-checks", "tasks done"],
			["square-check-big", "done task checkbox"],
			["calendar", "date schedule"],
			["clock", "time"],
			["timer", "time stopwatch"],
			["target", "goal aim"],
			["flag", "milestone"],
			["kanban", "board"],
			["rocket", "launch ship"],
			["lightbulb", "idea"],
			["trophy", "win award"],
		],
	},
	{
		label: "Data",
		icons: [
			["activity", "pulse runs"],
			["chart-line", "graph"],
			["chart-column", "graph bar"],
			["chart-pie", "graph"],
			["trending-up", "growth"],
			["gauge", "meter speed"],
			["database", "storage store"],
			["table", "grid spreadsheet"],
			["layers", "stack"],
			["sigma", "sum math"],
			["calculator", "math"],
			["hash", "number"],
		],
	},
	{
		label: "Dev",
		icons: [
			["cpu", "chip processor worker"],
			["code", "program"],
			["square-terminal", "shell console cli"],
			["braces", "json code"],
			["bug", "debug issue"],
			["scan-search", "lens inspect browse"],
			["git-branch", "version"],
			["server", "host"],
			["cloud", "remote"],
			["network", "graph nodes"],
			["workflow", "flow pipeline"],
			["box", "cell container"],
			["boxes", "containers"],
			["package", "box module"],
			["puzzle", "plugin extension"],
			["wrench", "tool fix"],
			["cog", "settings gear"],
			["zap", "fast power bolt"],
			["key", "secret"],
			["lock", "secure private"],
			["shield", "security"],
		],
	},
	{
		label: "Media",
		icons: [
			["image", "picture photo"],
			["camera", "photo"],
			["film", "movie video"],
			["music", "audio song"],
			["headphones", "audio listen"],
			["mic", "audio voice record"],
			["palette", "art colour design"],
			["pen-tool", "design draw"],
			["tv", "screen watch"],
			["gamepad-2", "game play"],
		],
	},
	{
		label: "People",
		icons: [
			["user", "person me profile"],
			["users", "team group people"],
			["contact", "person card"],
			["mail", "email letter"],
			["message-square", "chat comment"],
			["messages-square", "chat conversation"],
			["phone", "call"],
			["smile", "happy face"],
			["heart", "love like"],
			["handshake", "deal partner"],
		],
	},
	{
		label: "Places",
		icons: [
			["house", "home"],
			["building-2", "office company"],
			["store", "shop"],
			["globe", "world web"],
			["map", "travel"],
			["map-pin", "location place"],
			["compass", "explore direction"],
			["plane", "travel flight"],
			["mountain", "nature"],
			["trees", "nature forest"],
			["sun", "day weather"],
			["moon", "night"],
		],
	},
	{
		label: "Symbols",
		icons: [
			["star", "favourite"],
			["sparkles", "magic new"],
			["flame", "fire hot"],
			["leaf", "nature plant"],
			["sprout", "grow plant"],
			["coffee", "drink break"],
			["gift", "present"],
			["bell", "notify alert"],
			["hexagon", "shape"],
			["diamond", "shape"],
			["atom", "science"],
			["anchor", "harbour"],
			["feather", "light write"],
			["crown", "king"],
			["gem", "jewel"],
			["tag", "label"],
			["link", "url chain"],
			["search", "find"],
			["wallet", "money"],
			["coins", "money"],
		],
	},
];
