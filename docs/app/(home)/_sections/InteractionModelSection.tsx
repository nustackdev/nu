import { BookOpen } from 'lucide-react';
import { GithubMark } from '@/components/marks/GithubMark';
import {
  ActionRow,
  Cta,
  RepoName,
  SectionCard,
  SectionTitle,
} from './SectionCard';
import { ROOT, BRANCHES, LEAVES, HUE_VAR, type Atom } from './interactionAtoms.data';
import s from './InteractionModelSection.module.css';

/**
 * §1 — the interaction model.
 * Merged prose + viz in a single body: horizontal left-to-right SVG tree.
 * Nu → {Ref, Interaction} → {Query, Command, Action, Span, Flow}, each with
 * a 5-word blurb. Bezier connectors, hues from the fabric palette.
 */
export function InteractionModelSection() {
  return (
    <SectionCard hue="s1" vizHue="sage" id="interaction-model">
      <div className={s.centered}>
        <SectionTitle>We build on the Interaction Model</SectionTitle>

        <div className={s.tree}>
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

        <ActionRow>
          <Cta href="/docs">
            <BookOpen size={14} aria-hidden />
            <span>Read the model</span>
          </Cta>
          <Cta href="https://github.com/nustackdev/interaction-model">
            <GithubMark size={14} />
            <RepoName>nustackdev/interaction-model</RepoName>
          </Cta>
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
