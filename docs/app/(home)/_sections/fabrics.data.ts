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
    title: 'In-process address space.',
    body: 'Ephemeral Python-native store. Zero-config default for tests, notebooks, caches.',
    Viz: MemGlyph,
    docsHref: '/docs',
  },
  {
    name: 'virtuals',
    title: 'Persistent key-value space.',
    body: 'Virtual collections over any kv backend. One protocol, swappable engines.',
    backends: ['rocksdb', 'lmdb'],
    Viz: VirtualsGlyph,
    docsHref: '/docs',
  },
  {
    name: 'ray',
    title: 'Compute across the cluster.',
    body: 'Distribute work on Ray without leaving the interaction model.',
    Viz: RayGlyph,
    docsHref: '/docs',
  },
  {
    name: 'ui',
    title: 'Refs on screen.',
    body: 'Binds Nu Refs to live UI surfaces. Reads render, writes hit the DOM.',
    Viz: UiGlyph,
    docsHref: '/docs',
  },
  {
    name: 'invisibles',
    title: 'Location-transparent Nus.',
    body: 'Refs resolve across processes and machines. Call remote Nus like locals.',
    Viz: InvisiblesGlyph,
    docsHref: '/docs',
  },
];
