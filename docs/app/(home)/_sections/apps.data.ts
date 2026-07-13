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
    title: 'Logging built on Nu.',
    body: 'Structured logs as first-class Refs. Handles billions of entries without breaking a sweat. UI dashboard out of the box.',
    href: '/nulog',
    repo: 'https://github.com/nustackdev/nulog',
    Viz: NulogMockSvg,
  },
  {
    name: 'nuspace',
    title: 'A workspace for building on Nu.',
    body: 'The Nu programming model scaled into a knowledge base. Your everything base.',
    href: '/nuspace',
    repo: 'https://github.com/nustackdev/nuspace',
    Viz: NuspaceMockSvg,
  },
];
