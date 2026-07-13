import type { ComponentType } from 'react';
import {
  MemGlyph,
  VirtualsGlyph,
  InvisiblesGlyph,
  RayGlyph,
  UiGlyph,
} from '@/components/marks/FabricGlyphs';

export type Fabric = {
  name: string;
  title: string;
  body: string;
  backends?: string[];
  Viz: ComponentType;
  /** Docs URL for this fabric's own page. Points to /docs until per-fabric
   *  pages land. */
  docsHref: string;
};

export const FABRICS: Fabric[] = [
  {
    name: 'mem',
    title: 'In-process substrate.',
    body: 'Ephemeral Python-native store. Zero-config default for tests, notebooks, cache, etc.',
    Viz: MemGlyph,
    docsHref: '/docs',
  },
  {
    name: 'virtuals',
    title: 'Persistent substrate for Nu.',
    body: 'Virtual collections over any key-value storage. One protocol, swappable backends.',
    backends: ['rocksdb', 'lmdb'],
    Viz: VirtualsGlyph,
    docsHref: '/docs',
  },
  {
    name: 'ray',
    title: 'Compute across the cluster.',
    body: 'Scale Nu with Ray. Distribute work without leaving the interaction model.',
    Viz: RayGlyph,
    docsHref: '/docs',
  },
  {
    name: 'ui',
    title: 'Refs on screen.',
    body: 'A rendering fabric that binds Nu Refs to live UI surfaces.',
    Viz: UiGlyph,
    docsHref: '/docs',
  },
  {
    name: 'invisibles',
    title: 'Location-independent Nus.',
    body: 'Transparent RPC across processes and machines. Run Nus wherever you want.',
    Viz: InvisiblesGlyph,
    docsHref: '/docs',
  },
];
