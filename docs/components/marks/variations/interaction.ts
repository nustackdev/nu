import type { VizVariant } from './types';
import { OneLineSvg } from './interaction/one-line';
import { OneLineV1Svg } from './interaction/one-line-v1';
import { DiskToBrowserSvg } from './interaction/disk-to-browser';
import { ThreeFabricFanoutSvg } from './interaction/three-fabric-fanout';
import { BeforeAfterSvg } from './interaction/before-after';
import { ImperativeVsDeclarativeSvg } from './interaction/imperative-vs-declarative';
import { ValueTrajectorySvg } from './interaction/value-trajectory';
import { LayeredStackSvg } from './interaction/layered-stack';
import { InteractionAnatomySvg } from './interaction/interaction-anatomy';
import { AssemblyPiecesSvg } from './interaction/assembly-pieces';
import { SingleAddressAnatomySvg } from './interaction/single-address-anatomy';

export const INTERACTION_VARIANTS: VizVariant[] = [
  {
    title: 'One line, two places (v2 · hinted)',
    style: 'app.py · counter_ref.store(db_ref) · role-coded colors · long bottom leader',
    concept:
      'Refs and their hint chips in purple, the Interaction (.store call and its hint) in blue — one color per role. Long blue leader drops from .store through the gap between the two icons, landing on an `interaction` chip below the whole visualization.',
    Svg: OneLineSvg,
  },
  {
    title: 'One line, two places (v1 · unhinted)',
    style: 'zero chrome · sync.py · counter.store(rocksdb) · dotted links',
    concept:
      'The original stripped-down version — no chips, no annotations. `counter.store(rocksdb)` in a mini sync.py file with two dotted drops to a browser tab and rocksdb. Kept as fallback.',
    Svg: OneLineV1Svg,
  },
  {
    title: 'Disk → interaction → browser',
    style: 'two fabric panels · one interaction pill · same ref on both sides',
    concept:
      'A value on rocksdb, a Ref in the browser, and one Nu Interaction (`browser.value.store(disk.value)`) that reads disk and writes browser. Same Ref vocabulary on both sides — Refs, Interactions, unification in one glance.',
    Svg: DiskToBrowserSvg,
  },
  {
    title: 'Three-fabric fan-out',
    style: 'concrete · code strings · substrate icons · corner ticks · subtle pulse',
    concept:
      'Three fragmented raw APIs (input.value, db.put, dict[]) crossed out on the left collapse into one Nu Interaction, which fans out to browser, disk, and memory with the new value. Compressed version of the /nu TransitionViz.',
    Svg: ThreeFabricFanoutSvg,
  },
  {
    title: 'Before / after',
    style: 'paneled · concrete values · accent v1 · blink dot',
    concept:
      'Two panels — Context v0 { counter: 0 } and Context v1 { counter: 1 } — with `store(1)` on the arrow between them. Reads instantly as "an Interaction transitions the Context".',
    Svg: BeforeAfterSvg,
  },
  {
    title: 'Imperative vs declarative',
    style: 'split · fabric-tagged snippets · accent panel · vertical seam',
    concept:
      'Left column stacks three imperative snippets each tagged with its fabric, all crossed out. Right column shows one Nu Interaction covering all three. Answers "why use Nu at all?" in one glance.',
    Svg: ImperativeVsDeclarativeSvg,
  },
  {
    title: 'Value trajectory',
    style: 'timeline · labeled states · concrete values · pulse on second arrow',
    concept:
      'A single Ref (counter/value) drawn as a timeline: v0=0 → store(1) → v1=1 → store(value+42) → v2=43. Each transition is a labelled Interaction; the last state is accented.',
    Svg: ValueTrajectorySvg,
  },
  {
    title: 'Layered stack',
    style: 'three bands · cheatsheet · substrate glyphs · grid-free',
    concept:
      'Refs / Interactions / Fabrics as three horizontal bands. Each band shows its own glyphs (ref circles, interaction squares with `store(1)` / `+42` / `>>`, dashed fabric rectangles). A "what\'s what" cheatsheet.',
    Svg: LayeredStackSvg,
  },
  {
    title: 'Interaction anatomy',
    style: 'annotated expression · callouts · right-side legend',
    concept:
      'The expression `Add(counter, 1)` blown up with callouts pointing at each part: operator, ref, arg. A small legend on the right pins the model vocabulary (ref, interaction, fabric glyphs).',
    Svg: InteractionAnatomySvg,
  },
  {
    title: 'Assembly pieces',
    style: 'snap-notch pieces · assembled panel · nu.run arrow',
    concept:
      'Three snap-together pieces on the left (ref / interaction / fabric) → nu.run → an assembled working system on the right where value goes 0 → 1. Ties to the hero line "assemble, not write".',
    Svg: AssemblyPiecesSvg,
  },
  {
    title: 'Single-address anatomy',
    style: 'central ref · four callouts · dashed fabric container',
    concept:
      'One central Ref (`counter/value`) with four callouts: what it is (address, not value), current value, the Interaction acting on it (`store(1)`), and the Fabric it resolves inside.',
    Svg: SingleAddressAnatomySvg,
  },
];
