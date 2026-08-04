import { BookOpen } from 'lucide-react';
import { GithubMark } from '@/components/site/marks/GithubMark';
import { SiteButton, SiteButtonRepoLabel } from '@/components/site/SiteButton';
import {
  ActionRow,
  SectionCard,
  SectionTitle,
} from './SectionCard';
import { ROOT, BRANCHES, LEAVES, HUE_VAR, type Atom } from './interactionAtoms.data';
import s from './InteractionModelSection.module.css';

/**
 * §1 — the interaction model.
 * Desktop: horizontal SVG tree, Nu → {Ref, Interaction} → 5 leaves.
 * Mobile:  vertical cascade outline, leaves indented under Interaction with a tree line.
 * Same 8 atoms, same blurbs, only the layout switches at 720px.
 */
export function InteractionModelSection() {
  return (
    <SectionCard hue="s1" vizHue="sage" id="interaction-model">
      <div className={s.centered}>
        <SectionTitle>We build on the Interaction Model</SectionTitle>

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

        <ActionRow>
          <SiteButton href="/docs">
            <BookOpen size={14} aria-hidden />
            <span>Read the model</span>
          </SiteButton>
          <SiteButton href="https://github.com/nustackdev/interaction-model">
            <GithubMark size={14} />
            <SiteButtonRepoLabel>nustackdev/interaction-model</SiteButtonRepoLabel>
          </SiteButton>
        </ActionRow>
      </div>
    </SectionCard>
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
