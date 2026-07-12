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
};

export const FABRICS: Fabric[] = [
  {
    name: 'mem',
    title: 'In-process substrate.',
    body: 'Ephemeral Python-native store. Zero-config default for tests, notebooks, and small runtimes.',
    Viz: MemGlyph,
  },
  {
    name: 'virtuals',
    title: 'Persistent substrate for Shapes.',
    body: 'Virtual collections over any tuple-key storage. One protocol, swappable backends.',
    backends: ['rocksdb', 'lmdb', 'acid-inmem', 'text'],
    Viz: VirtualsGlyph,
  },
  {
    name: 'invisibles',
    title: 'Location-independent Nus.',
    body: 'Transparent RPC across processes and machines. Same object, same code, different site.',
    Viz: InvisiblesGlyph,
  },
  {
    name: 'ray',
    title: 'Compute across the cluster.',
    body: 'Nu Ops scale onto Ray. Distribute work without leaving the interaction model.',
    Viz: RayGlyph,
  },
  {
    name: 'ui',
    title: 'Refs on screen.',
    body: 'A rendering fabric that binds Nu Refs to live UI surfaces. Value changes flow through.',
    Viz: UiGlyph,
  },
];
