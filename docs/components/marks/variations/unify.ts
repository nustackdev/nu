import type { VizVariant } from './types';
import { DiskToBrowserSvg } from './interaction/disk-to-browser';
import { VerticalStackSvg } from './unify/vertical-stack';
import { SplitBrainSvg } from './unify/split-brain';
import { SharedRefBannerSvg } from './unify/shared-ref-banner';
import { PhysicalFormsSvg } from './unify/physical-forms';
import { RefSatelliteSvg } from './unify/ref-satellite';
import { RefIdentitySvg } from './unify/ref-identity';
import { BidirectionalLoopSvg } from './unify/bidirectional-loop';
import { ReadThroughCacheSvg } from './unify/read-through-cache';
import { ConvergingVSvg } from './unify/converging-v';

export const UNIFY_VARIANTS: VizVariant[] = [
  {
    title: 'Disk → interaction → browser (seed)',
    style: 'two fabric panels · one interaction pill · same ref on both sides',
    concept:
      'A value on rocksdb, a Ref in the browser, and one Nu Interaction (`browser.value.store(disk.value)`) that reads disk and writes browser. Same Ref vocabulary on both sides — Refs, Interactions, unification in one glance.',
    Svg: DiskToBrowserSvg,
  },
  {
    title: 'Vertical stack',
    style: 'vertical · disk on top · browser bottom · pulse',
    concept:
      'Disk fabric on top, one Nu Interaction (`browser.value.store(disk.value)`) in the middle, browser fabric at the bottom — same Ref both sides, vertical rhythm instead of horizontal.',
    Svg: VerticalStackSvg,
  },
  {
    title: 'Split-brain reconciliation',
    style: 'before-after · two rows · diverged ≠ then unified ≡',
    concept:
      'Two fabrics diverge (disk 42, browser 0). One Nu Interaction runs; the after row shows both holding 42 under a purple ≡. Divergence made visible, then reconciled.',
    Svg: SplitBrainSvg,
  },
  {
    title: 'Shared ref banner',
    style: 'top banner · hairline drops · three fabric cards',
    concept:
      'A big top banner pins the shared Ref counter/value. Disk, browser, and memory cards hang below on hairline drops, each holding 42 — one address, resolved through many fabrics.',
    Svg: SharedRefBannerSvg,
  },
  {
    title: 'Different physical forms',
    style: 'bytes · dom · one interaction bridges both',
    concept:
      'Left panel shows `00 00 00 2a` bytes on rocksdb. Right panel shows `<span>42</span>` in the browser DOM. One Nu Interaction labels both as the same Ref — physical form differs, address does not.',
    Svg: PhysicalFormsSvg,
  },
  {
    title: 'Ref satellite',
    style: 'centered ref circle · spokes · four fabrics',
    concept:
      'The Ref sits at the center; disk, browser, memory, and network are satellites on dashed spokes. Below, one Nu Interaction reifies the equivalence between disk and browser — Ref is the center, fabrics are the resolutions.',
    Svg: RefSatelliteSvg,
  },
  {
    title: 'Ref identity ≡',
    style: 'two panels · giant ≡ · interaction reifies',
    concept:
      'Two fabric panels flank a giant purple ≡ over the label "same address · different fabric". Below, the Nu Interaction `browser.value.store(disk.value)` reifies the equivalence in code.',
    Svg: RefIdentitySvg,
  },
  {
    title: 'Bidirectional loop',
    style: 'two panels · two interactions · curved rails · loop',
    concept:
      'Browser and disk both hold Ref counter/value. Top rail: on browser change, disk.value.store(browser.value). Bottom rail: on disk change, browser.value.store(disk.value). Two Interactions form a two-way binding under one Ref vocabulary.',
    Svg: BidirectionalLoopSvg,
  },
  {
    title: 'Read-through cache',
    style: 'numbered steps · miss · load · store',
    concept:
      'Step 1 browser.value.load() returns EMPTY. Step 2 one Nu Interaction reaches disk and stores the result back into browser. Step 3 browser now holds 42. The bracket-tree summary sits below: `browser.value.store(disk.value.load())`.',
    Svg: ReadThroughCacheSvg,
  },
  {
    title: 'Converging V',
    style: 'apex interaction · two bottom fabrics · unified value drops',
    concept:
      'One Nu Interaction sits at the apex; disk and browser panels sit at the bottom-left and bottom-right. Two converging rails feed into the pill, one arrow drops through the middle carrying the unified 42.',
    Svg: ConvergingVSvg,
  },
];
