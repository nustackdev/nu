// Public entry for @nustackdev/ui-kit.
//
// The kit ships these surfaces:
//   - tree        : the tree store bindings, registry and NodeView
//   - nodes       : every node type the kit registers (import for the side effect)
//   - components  : primitives (Badge, Card, Switch, ...) and shared shell bits
//   - lib/utils   : the `cn()` helper and the shared focus-ring variant map
//
// Tokens live in ./index.css, the Tailwind theme and `scrollbar-none` in
// ./theme.css. Both compile into dist/styles.css, which consumers import
// separately as `@nustackdev/ui-kit/styles`.

export { ErrorBoundary } from "./components/ErrorBoundary";
export {
	Accordion,
	AccordionContent,
	AccordionItem,
	AccordionTrigger,
} from "./components/ui/accordion";
export {
	Alert,
	AlertDescription,
	AlertIcon,
	AlertTitle,
	alertVariants,
} from "./components/ui/alert";
export { Avatar, AvatarFallback, AvatarImage } from "./components/ui/avatar";
export { Badge, badgeVariants } from "./components/ui/badge";
export {
	Breadcrumb,
	BreadcrumbEllipsis,
	BreadcrumbItem,
	BreadcrumbLink,
	BreadcrumbList,
	BreadcrumbPage,
	BreadcrumbSeparator,
} from "./components/ui/breadcrumb";
export { Button, buttonVariants } from "./components/ui/button";
export {
	Card,
	CardAction,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
	cardVariants,
} from "./components/ui/card";
export {
	Chart,
	type ChartClick,
	type ChartHandle,
	type ChartOption,
	type ChartProps,
} from "./components/ui/chart";
export { Checkbox, checkboxVariants } from "./components/ui/checkbox";
export type { CodeProps } from "./components/ui/code";
export { Code } from "./components/ui/code";
export {
	Collapsible,
	CollapsibleContent,
	CollapsibleTrigger,
} from "./components/ui/collapsible";
export {
	Combobox,
	ComboboxContent,
	ComboboxEmpty,
	ComboboxGroup,
	ComboboxInput,
	ComboboxItem,
	ComboboxList,
	ComboboxTrigger,
} from "./components/ui/combobox";
export {
	CommandEmpty,
	CommandGroup,
	CommandInput,
	CommandItem,
	CommandList,
	CommandPalette,
	CommandSeparator,
	CommandShortcut,
	commandHeadingClasses,
	commandItemClasses,
	commandSurfaceClasses,
	useCommandPaletteHotkey,
} from "./components/ui/command-palette";
export {
	ContextMenu,
	ContextMenuCheckboxItem,
	ContextMenuContent,
	ContextMenuGroup,
	ContextMenuItem,
	ContextMenuLabel,
	ContextMenuRadioGroup,
	ContextMenuRadioItem,
	ContextMenuSeparator,
	ContextMenuShortcut,
	ContextMenuSub,
	ContextMenuSubContent,
	ContextMenuSubTrigger,
	ContextMenuTrigger,
} from "./components/ui/context-menu";
export {
	DataTable,
	type DataTableColumn,
	type DataTableEdit,
	type DataTableHandle,
	type DataTableKind,
	type DataTableProps,
	type DataTableRow,
	type DataTableSort,
} from "./components/ui/data-table";
export { DatePicker, DateRangePicker } from "./components/ui/date-picker";
export {
	Dialog,
	DialogClose,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogOverlay,
	DialogTitle,
	DialogTrigger,
	dialogContentVariants,
} from "./components/ui/dialog";
export {
	DropdownMenu,
	DropdownMenuCheckboxItem,
	DropdownMenuContent,
	DropdownMenuGroup,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuRadioGroup,
	DropdownMenuRadioItem,
	DropdownMenuSeparator,
	DropdownMenuShortcut,
	DropdownMenuSub,
	DropdownMenuSubContent,
	DropdownMenuSubTrigger,
	DropdownMenuTrigger,
	menuContentClasses,
	menuItemClasses,
	menuItemDangerClasses,
	menuSeparatorClasses,
	menuShortcutClasses,
} from "./components/ui/dropdown-menu";
export { EmptyState, emptyStateVariants } from "./components/ui/empty-state";
export { Gauge, gaugeVariants } from "./components/ui/gauge";
export {
	Grid,
	type GridProps,
	gridSpan,
	trackCount,
	useTrackCount,
} from "./components/ui/grid";
export { Heading, headingVariants } from "./components/ui/heading";
export { Html, type HtmlProps } from "./components/ui/html";
export {
	frameVariants as iconFrameVariants,
	Icon,
	type IconProps,
	iconVariants,
} from "./components/ui/icon";
export { IconButton, iconButtonVariants } from "./components/ui/icon-button";
export { Image } from "./components/ui/image";
export { InlineEdit, type InlineEditProps } from "./components/ui/inline-edit";
export { Input, inputVariants } from "./components/ui/input";
export { JsonView } from "./components/ui/json-view";
export { Kbd, type KbdProps, kbdVariants } from "./components/ui/kbd";
export { Line, type LineProps } from "./components/ui/line";
export {
	List,
	ListItem,
	type ListProps,
	type ListVariant,
	listVariants,
} from "./components/ui/list";
export type { MarkdownProps } from "./components/ui/markdown";
export { Markdown } from "./components/ui/markdown";
export {
	Container,
	type ContainerPadding,
	type ContainerProps,
	PAGE_WIDTH_CLASSES,
	type PageWidth,
} from "./components/ui/container";
export { NavLink, navLinkVariants } from "./components/ui/nav-link";
export { NumberInput, numberInputVariants } from "./components/ui/number-input";
export type { OverflowTooltipProps } from "./components/ui/overflow-tooltip";
export { OverflowTooltip } from "./components/ui/overflow-tooltip";
export { PageLink, type PageLinkProps, pageLinkVariants } from "./components/ui/page-link";
export {
	Panel,
	PanelContent,
	PanelDescription,
	PanelFooter,
	PanelHeader,
	PanelTitle,
	panelVariants,
} from "./components/ui/panel";
export {
	Popover,
	PopoverAnchor,
	PopoverArrow,
	PopoverClose,
	PopoverContent,
	PopoverTrigger,
} from "./components/ui/popover";
export { Progress, progressVariants } from "./components/ui/progress";
export { Prose } from "./components/ui/prose";
export {
	RadioGroup,
	RadioGroupItem,
	radioGroupItemVariants,
} from "./components/ui/radio-group";
export {
	ResizableHandle,
	type ResizableHandleProps,
	type ResizableOrientation,
	type ResizableOverflow,
	ResizablePanel,
	ResizablePanelGroup,
	type ResizablePanelGroupHandle,
	type ResizablePanelGroupProps,
	type ResizablePanelProps,
	type ResizableSize,
} from "./components/ui/resizable";
export { Section, sectionVariants } from "./components/ui/section";
export {
	Select,
	SelectContent,
	SelectGroup,
	SelectItem,
	SelectLabel,
	SelectSeparator,
	SelectTrigger,
	SelectValue,
} from "./components/ui/select";
export { Separator } from "./components/ui/separator";
export {
	Sheet,
	SheetClose,
	SheetContent,
	SheetDescription,
	SheetFooter,
	SheetHeader,
	SheetTitle,
	SheetTrigger,
	sheetContentVariants,
} from "./components/ui/sheet";
export { Shortcut, type ShortcutProps } from "./components/ui/shortcut";
export { Skeleton } from "./components/ui/skeleton";
export { SketchBoard, type SketchBoardProps } from "./components/ui/sketch-board";
export {
	normalizeElements as normalizeSketchElements,
	SKETCH_CONTROLS,
	SKETCH_FILLS,
	SKETCH_SIZES,
	SKETCH_STROKES,
	SKETCH_TOOLS,
	type SketchControl,
	type SketchDefaults,
	type SketchElement,
	type SketchPoint,
	type SketchTool,
	sketchColor,
} from "./components/ui/sketch-board-model";
export { Slider, sliderVariants } from "./components/ui/slider";
export { Spinner, spinnerVariants } from "./components/ui/spinner";
export { Stat, StatDelta, StatLabel, StatValue } from "./components/ui/stat";
export { StatusDot, statusDotVariants } from "./components/ui/status-dot";
export { StatusPill, statusPillVariants } from "./components/ui/status-pill";
export { Switch, switchVariants } from "./components/ui/switch";
export {
	Table,
	TableBody,
	TableCaption,
	TableCell,
	TableFooter,
	TableHead,
	TableHeader,
	TableRow,
	tableVariants,
} from "./components/ui/table";
export {
	type ColumnAlign,
	type ColumnKind,
	type ColumnMenuActions,
	columnMenu,
	type RowMenuActions,
	rowMenu,
	type TableAction,
	type TableAnchor,
	type TableChoice,
	type TableHandleKind,
	TableHandles,
	type TableHandlesHandle,
	type TableHandlesProps,
	TableMenuContextItems,
	TableMenuDropdownItems,
	type TableMenuItem,
	type TableMenuItems,
	tableMenuKey,
	tableMenuKeys,
	tableMenuText,
} from "./components/ui/table-handles";
export {
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
	tabsListVariants,
} from "./components/ui/tabs";
export { TagInput, tagInputVariants } from "./components/ui/tag-input";
export { Text, textVariants } from "./components/ui/text";
export { TextArea, textAreaVariants } from "./components/ui/text-area";
export { Toggle, toggleVariants } from "./components/ui/toggle";
export {
	Tooltip,
	TooltipContent,
	TooltipProvider,
	TooltipTrigger,
} from "./components/ui/tooltip";
export {
	Tree,
	type TreeHandle,
	TreeItem,
	type TreeItemProps,
	type TreeItemState,
	type TreeProps,
} from "./components/ui/tree";
export type { TreeMove, TreeRow, TreeSource } from "./components/ui/tree-model";
export {
	type AnchorProps,
	type AnchorTarget,
	anchorProps,
	crossHost,
	normTarget,
	resolveHref,
	sameOrigin,
} from "./lib/anchor";
export { registerChartMap } from "./lib/chart/load";
export { mergeOption } from "./lib/chart/option";
export { type ChartTokens, chartTheme, readChartTokens } from "./lib/chart/theme";
export { loadLanguage } from "./lib/code/languages";
export { kitHighlight, kitTheme } from "./lib/code/theme";
export type { KeyBindings, KeyScope } from "./lib/keyboard";
export { useKeyScope } from "./lib/keyboard";
export type { ProseEditorProps } from "./lib/markdown/editor";
export { ProseEditor } from "./lib/markdown/editor";
export type { Markdown as MarkdownCodec, Parsed, SourceMap } from "./lib/markdown/markdown";
export { createMarkdown, markdown } from "./lib/markdown/markdown";
export { placeholder as prosePlaceholder, proseInputRules } from "./lib/markdown/rules";
export type { ProseClasses, ProseSchema } from "./lib/markdown/schema";
export { createProseSchema, proseRecipes, proseSchema, safeUrl } from "./lib/markdown/schema";
export {
	CLICK_SLOP,
	type DragAxis,
	readStored,
	SIDEBAR_WIDTH,
	splitHandleClasses,
	trackDrag,
	writeStored,
} from "./lib/resize";
export {
	ROVING_KEY,
	type RovingFocus,
	type RovingOptions,
	useRovingFocus,
} from "./lib/roving";
export { formatShortcut, isMac, keyLabel, keySpoken, type Platform } from "./lib/shortcut";
export { cn, ringVariants } from "./lib/utils";
export { nodeEntries } from "./nodes";
export type { LensColumnsProps } from "./nodes/output/lens/columns";
export { LensColumns } from "./nodes/output/lens/columns";
export type { Column as LensColumn, Entry as LensEntry } from "./nodes/output/lens/types";
export * from "./tree";
