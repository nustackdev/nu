import s from './InteractionModelDiagram.module.css';

/**
 * InteractionModelDiagram — Nu → {Ref, Interaction} → {Query, Command, Action,
 * Span, Flow}. Desktop: horizontal SVG tree with absolutely-positioned labels
 * over connector paths. Mobile (< 720px): vertical cascade outline.
 *
 * Lifted from app/old_home/_sections/InteractionModelSection.tsx. The 8-atom
 * vocabulary is baked in below (previously in interactionAtoms.data.ts).
 */

type Hue = 'ink' | 'ink2' | 'sage' | 'teal' | 'plum' | 'amber' | 'steel';

type Atom = {
  label: string;
  blurb: string;
  hue: Hue;
};

const ROOT: Atom = { label: 'Nu', blurb: 'the one core atom', hue: 'ink' };

const BRANCHES: Atom[] = [
  { label: 'Ref',         blurb: 'address to any resource', hue: 'sage' },
  { label: 'Interaction', blurb: 'the work over refs',      hue: 'ink2' },
];

const LEAVES: Atom[] = [
  { label: 'Query',   blurb: 'pure evaluation, yields values', hue: 'teal'  },
  { label: 'Command', blurb: 'mutation, yields nothing',       hue: 'plum'  },
  { label: 'Action',  blurb: 'mutation, yields values',        hue: 'amber' },
  { label: 'Span',    blurb: 'scope wrapping a body',          hue: 'steel' },
  { label: 'Flow',    blurb: 'orchestration of mutations',     hue: 'steel' },
];

const HUE_VAR: Record<Hue, string> = {
  ink:   'var(--nu-ink)',
  ink2:  'var(--nu-ink-2)',
  sage:  'var(--nu-hue-sage)',
  teal:  'var(--nu-hue-teal)',
  plum:  'var(--nu-hue-plum)',
  amber: 'var(--nu-hue-amber)',
  steel: 'var(--nu-hue-steel)',
};

export function InteractionModelDiagram({ className }: { className?: string }) {
  const cls = [s.root, className].filter(Boolean).join(' ');
  return (
    <div className={cls}>
      <div className={s.treeDesktop}>
        <svg
          className={s.connectors}
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          aria-hidden
        >
          <path d="M 13 50 C 22 50 22 28 30 28" />
          <path d="M 13 50 C 22 50 22 72 30 72" />
          <path d="M 54 72 C 61 72 61 10 68 10" />
          <path d="M 54 72 C 61 72 61 30 68 30" />
          <path d="M 54 72 C 61 72 61 50 68 50" />
          <path d="M 54 72 C 61 72 61 70 68 70" />
          <path d="M 54 72 C 61 72 61 90 68 90" />
        </svg>

        <Node atom={ROOT}        size="root"   left="2%"  top="50%" />
        <Node atom={BRANCHES[0]} size="branch" left="31%" top="28%" />
        <Node atom={BRANCHES[1]} size="branch" left="31%" top="72%" />
        <Node atom={LEAVES[0]}   size="leaf"   left="70%" top="10%" />
        <Node atom={LEAVES[1]}   size="leaf"   left="70%" top="30%" />
        <Node atom={LEAVES[2]}   size="leaf"   left="70%" top="50%" />
        <Node atom={LEAVES[3]}   size="leaf"   left="70%" top="70%" />
        <Node atom={LEAVES[4]}   size="leaf"   left="70%" top="90%" />
      </div>

      <div className={s.treeMobile}>
        <div className={s.mRoot}>
          <div className={s.mRootLabel} style={{ color: HUE_VAR[ROOT.hue] }}>
            {ROOT.label}
          </div>
          <div className={s.mBlurb}>{ROOT.blurb}</div>
        </div>

        {BRANCHES.map((b) => (
          <div key={b.label} className={s.mBranch}>
            <div className={s.mBranchLabel} style={{ color: HUE_VAR[b.hue] }}>
              {b.label}
            </div>
            <div className={s.mBlurb}>{b.blurb}</div>
          </div>
        ))}

        <ul className={s.mLeaves}>
          {LEAVES.map((l) => (
            <li key={l.label} className={s.mLeaf}>
              <div className={s.mLeafLabel} style={{ color: HUE_VAR[l.hue] }}>
                {l.label}
              </div>
              <div className={s.mBlurb}>{l.blurb}</div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

const SIZE_CLASS: Record<'root' | 'branch' | 'leaf', string> = {
  root:   s.sizeRoot,
  branch: s.sizeBranch,
  leaf:   s.sizeLeaf,
};

function Node({
  atom, size, left, top,
}: {
  atom: Atom;
  size: 'root' | 'branch' | 'leaf';
  left: string;
  top: string;
}) {
  return (
    <div className={`${s.node} ${SIZE_CLASS[size]}`} style={{ left, top }}>
      <div className={s.label} style={{ color: HUE_VAR[atom.hue] }}>
        {atom.label}
      </div>
      <div className={s.blurb}>{atom.blurb}</div>
    </div>
  );
}
