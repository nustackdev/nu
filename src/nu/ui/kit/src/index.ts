// Public entry for @nustackdev/ui-kit.
//
// The kit ships four surfaces:
//   - refs        : factory + renderer registries for every Ref type
//   - store       : zustand + immer store bound to the wire protocol
//   - components  : primitives (Badge, Card, Switch, ...) and shared shell bits
//   - lib/utils   : the `cn()` helper
//
// Tailwind tokens live in ./index.css; consumers import that separately.

export * from "./refs";
export { useStore } from "./store";
export { cn } from "./lib/utils";
export { ErrorBoundary } from "./components/ErrorBoundary";
export { FieldView } from "./components/FieldView";
export { Badge, badgeVariants } from "./components/ui/badge";
export { Button, buttonVariants } from "./components/ui/button";
export {
	Accordion,
	AccordionContent,
	AccordionItem,
	AccordionTrigger,
} from "./components/ui/accordion";
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
	Collapsible,
	CollapsibleContent,
	CollapsibleTrigger,
} from "./components/ui/collapsible";
export { Checkbox, checkboxVariants } from "./components/ui/checkbox";
export { IconButton, iconButtonVariants } from "./components/ui/icon-button";
export { Input, inputVariants } from "./components/ui/input";
export { Kbd } from "./components/ui/kbd";
export { NumberInput, numberInputVariants } from "./components/ui/number-input";
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
	RadioGroup,
	RadioGroupItem,
	radioGroupItemVariants,
} from "./components/ui/radio-group";
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
export { DatePicker, DateRangePicker } from "./components/ui/date-picker";
export { TagInput, tagInputVariants } from "./components/ui/tag-input";
export { Slider, sliderVariants } from "./components/ui/slider";
export { Switch, switchVariants } from "./components/ui/switch";
export {
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
	tabsListVariants,
} from "./components/ui/tabs";
export { TextArea, textAreaVariants } from "./components/ui/text-area";
export { Toggle, toggleVariants } from "./components/ui/toggle";
export {
	Alert,
	AlertIcon,
	AlertTitle,
	AlertDescription,
	alertVariants,
} from "./components/ui/alert";
export { Progress, progressVariants } from "./components/ui/progress";
export { Spinner, spinnerVariants } from "./components/ui/spinner";
export { Skeleton } from "./components/ui/skeleton";
export { Avatar, AvatarImage, AvatarFallback } from "./components/ui/avatar";
export { Separator } from "./components/ui/separator";
export { Heading, headingVariants } from "./components/ui/heading";
export { Text, textVariants } from "./components/ui/text";
export { Code } from "./components/ui/code";
export { JsonView } from "./components/ui/json-view";
export { Gauge, gaugeVariants } from "./components/ui/gauge";
export { Stat, StatLabel, StatValue, StatDelta } from "./components/ui/stat";
export { Prose } from "./components/ui/prose";
export { Image } from "./components/ui/image";
export {
	Table,
	TableHeader,
	TableBody,
	TableFooter,
	TableRow,
	TableHead,
	TableCell,
	TableCaption,
	tableVariants,
} from "./components/ui/table";
export { LineChart } from "./components/ui/line-chart";
export { BarChart } from "./components/ui/bar-chart";
export { AreaChart } from "./components/ui/area-chart";
export { PieChart } from "./components/ui/pie-chart";
export { Sparkline } from "./components/ui/sparkline";
export { NavLink, navLinkVariants } from "./components/ui/nav-link";
export {
	Breadcrumb,
	BreadcrumbList,
	BreadcrumbItem,
	BreadcrumbLink,
	BreadcrumbPage,
	BreadcrumbSeparator,
	BreadcrumbEllipsis,
} from "./components/ui/breadcrumb";
export { StatusPill, statusPillVariants } from "./components/ui/status-pill";
export {
	Dialog,
	DialogTrigger,
	DialogContent,
	DialogHeader,
	DialogFooter,
	DialogTitle,
	DialogDescription,
	DialogClose,
	DialogOverlay,
	dialogContentVariants,
} from "./components/ui/dialog";
export {
	Sheet,
	SheetTrigger,
	SheetContent,
	SheetHeader,
	SheetFooter,
	SheetTitle,
	SheetDescription,
	SheetClose,
	sheetContentVariants,
} from "./components/ui/sheet";
export {
	Popover,
	PopoverTrigger,
	PopoverContent,
	PopoverAnchor,
	PopoverArrow,
	PopoverClose,
} from "./components/ui/popover";
export {
	Tooltip,
	TooltipTrigger,
	TooltipContent,
	TooltipProvider,
} from "./components/ui/tooltip";
export {
	DropdownMenu,
	DropdownMenuTrigger,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuCheckboxItem,
	DropdownMenuRadioGroup,
	DropdownMenuRadioItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuGroup,
	DropdownMenuSub,
	DropdownMenuSubTrigger,
	DropdownMenuSubContent,
	DropdownMenuShortcut,
} from "./components/ui/dropdown-menu";
export {
	ContextMenu,
	ContextMenuTrigger,
	ContextMenuContent,
	ContextMenuItem,
	ContextMenuCheckboxItem,
	ContextMenuRadioGroup,
	ContextMenuRadioItem,
	ContextMenuLabel,
	ContextMenuSeparator,
	ContextMenuGroup,
	ContextMenuSub,
	ContextMenuSubTrigger,
	ContextMenuSubContent,
	ContextMenuShortcut,
} from "./components/ui/context-menu";
export {
	CommandPalette,
	CommandInput,
	CommandList,
	CommandEmpty,
	CommandGroup,
	CommandItem,
	CommandSeparator,
	CommandShortcut,
	useCommandPaletteHotkey,
} from "./components/ui/command-palette";
