/** Vocabulary for the interaction-model section: 8 atoms, hues, one-line blurbs. */

export type Hue = 'ink' | 'ink2' | 'sage' | 'teal' | 'plum' | 'amber' | 'steel';

export type Atom = {
  label: string;
  blurb: string;
  hue: Hue;
};

export const ROOT: Atom = {
  label: 'Nu',
  blurb: 'the one core atom',
  hue: 'ink',
};

export const BRANCHES: Atom[] = [
  { label: 'Ref',         blurb: 'address to any resource', hue: 'sage' },
  { label: 'Interaction', blurb: 'the work over refs',      hue: 'ink2' },
];

export const LEAVES: Atom[] = [
  { label: 'Query',   blurb: 'pure evaluation, yields values', hue: 'teal'  },
  { label: 'Command', blurb: 'mutation, yields nothing',       hue: 'plum'  },
  { label: 'Action',  blurb: 'mutation, yields values',        hue: 'amber' },
  { label: 'Span',    blurb: 'scope wrapping a body',          hue: 'steel' },
  { label: 'Flow',    blurb: 'orchestration of mutations',     hue: 'steel' },
];

export const HUE_VAR: Record<Hue, string> = {
  ink:   'var(--nu-ink)',
  ink2:  'var(--nu-ink-2)',
  sage:  'var(--nu-hue-sage)',
  teal:  'var(--nu-hue-teal)',
  plum:  'var(--nu-hue-plum)',
  amber: 'var(--nu-hue-amber)',
  steel: 'var(--nu-hue-steel)',
};
