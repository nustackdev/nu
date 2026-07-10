import type { VizVariant } from './types';
import { AppShelfSvg } from './apps/app-shelf';
import { NulogMockSvg } from './apps/nulog-mock';
import { SharedAlphabetSvg } from './apps/shared-alphabet';
import { AppAnatomySvg } from './apps/app-anatomy';
import { CompositionSlotsSvg } from './apps/composition-slots';
import { StackLayersSvg } from './apps/stack-layers';
import { FamilyTreeSvg } from './apps/family-tree';
import { TimelineSvg } from './apps/timeline';

export const APPS_VARIANTS: VizVariant[] = [
  {
    title: 'App shelf on Nu',
    style: 'shelf · substrate wash · trunks · live dots',
    concept:
      'Three app cells (nulog, nuspace, more) rest on a purple-wash Nu substrate; hairline trunks root each into nu.',
    Svg: AppShelfSvg,
  },
  {
    title: 'nulog running',
    style: 'browser mock · log rows · live pulse · footer strip',
    concept:
      'A real product screen — browser chrome + five structured log rows + footer naming shape + fabric — so the viewer instantly reads "these are shipped apps."',
    Svg: NulogMockSvg,
  },
  {
    title: 'Shared alphabet',
    style: 'two-panel · palette + apps · same glyphs',
    concept:
      'Primitives on the left (ref, interaction, shape, fabric); on the right, nulog and nuspace composed from the same glyphs — learn one alphabet, know every app.',
    Svg: SharedAlphabetSvg,
  },
  {
    title: 'Anatomy of an app',
    style: 'single-canvas · labeled rows · shape → refs → interaction → fabric',
    concept:
      'A cross-section of nulog: Log shape at the top, its refs, the append interaction, the rocksdb fabric — each labeled in Nu vocabulary.',
    Svg: AppAnatomySvg,
  },
  {
    title: 'Composition slots',
    style: 'fabric row + subset brackets',
    concept:
      'The five Nu fabrics sit in a row; brackets show which subsets nulog and nuspace pick — each app is a chord of the same instrument.',
    Svg: CompositionSlotsSvg,
  },
  {
    title: 'The stack',
    style: 'horizontal bands · model / nu / apps',
    concept:
      'Three stacked layers, bottom → top: the interaction model, Nu with its fabrics, the apps row — a layer-cake cheatsheet.',
    Svg: StackLayersSvg,
  },
  {
    title: 'Family tree from nu',
    style: 'root + branches · annotated edges · live pills',
    concept:
      'nu at the root; nulog and nuspace branch down as live children (with dimmed more), each edge annotated by what the app inherits.',
    Svg: FamilyTreeSvg,
  },
  {
    title: 'Roster timeline',
    style: 'horizontal axis · milestone ticks · nu-origin wash',
    concept:
      'Timeline with nu at origin; nulog and nuspace are live milestones, more is a dimmed tbd — the honest roster, no vaporware.',
    Svg: TimelineSvg,
  },
];
