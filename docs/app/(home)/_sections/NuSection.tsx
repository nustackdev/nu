import { GithubMark } from '@/components/marks/GithubMark';
import {
  ActionRow,
  Cta,
  CtaGhost,
  SectionCard,
  SectionCol,
  SectionIntro,
  SectionSplit,
  SectionTitle,
  SectionVisual,
} from './SectionCard';
import { NuCodeSample } from './NuCodeSample';

const FABRICS = ['shapes', 'mem', 'nudle', 'apps', 'lens'];

/**
 * §2 — Nu, the implementation.
 * Code LEFT (via `flip`), text RIGHT. Purple hue (s2).
 */
export function NuSection() {
  return (
    <SectionCard hue="s2" id="nu">
      <SectionSplit flip>
        <SectionVisual>
          <NuCodeSample />
        </SectionVisual>
        <SectionCol>
          <SectionTitle>Nu — the interaction model, made real.</SectionTitle>
          <SectionIntro>
            Nu ships the model in pure Python and grows it into a small stack
            of <b>fabrics</b> ({FABRICS.join(' · ')}) — everything else we
            make stands on this.
          </SectionIntro>
          <ActionRow>
            <Cta href="/docs">
              <span>meet Nu</span>
            </Cta>
            <CtaGhost href="https://github.com/nustackdev/nu">
              <GithubMark size={14} />
              <span>github</span>
            </CtaGhost>
          </ActionRow>
        </SectionCol>
      </SectionSplit>
    </SectionCard>
  );
}
