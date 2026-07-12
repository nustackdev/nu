import type { ComponentType } from 'react';
import { NulogMockSvg } from '@/components/marks/NulogMock';
import { NuspaceMockSvg } from '@/components/marks/NuspaceMock';

export type App = {
  name: string;
  title: string;
  body: string;
  href: string;
  repo: string;
  Viz: ComponentType;
};

export const APPS: App[] = [
  {
    name: 'nulog',
    title: 'Logging built on Nu shapes.',
    body: 'Structured logs as first-class Refs. One shape end-to-end — capture, query, ship.',
    href: '/nulog',
    repo: 'https://github.com/nustackdev/nulog',
    Viz: NulogMockSvg,
  },
  {
    name: 'nuspace',
    title: 'A workspace for building on Nu.',
    body: 'Apps, tabs, and data live under one roof. Nudle-native. Composable, inspectable.',
    href: '/nuspace',
    repo: 'https://github.com/nustackdev/nuspace',
    Viz: NuspaceMockSvg,
  },
];
