import { NustackMark } from '@/components/marks/NustackMark';
import { GithubMark } from '@/components/marks/GithubMark';
import { OneLineSvg } from '@/components/marks/OneLine';
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
  VizFrame,
} from './SectionCard';

/**
 * §1 — the interaction model.
 * Text LEFT, one-line viz RIGHT. Blue hue (s1).
 */
export function InteractionModelSection() {
  return (
    <SectionCard hue="s1" id="interaction-model">
      <SectionSplit>
        <SectionCol>
          <SectionTitle>We build on the interaction model.</SectionTitle>
          <SectionIntro>
            A tiny theory of computation: <b>Refs</b> address values,{' '}
            <b>Interactions</b> change them, <b>Fabrics</b> are the worlds
            those addresses resolve inside. Everything else at{' '}
            <NustackMark /> is a faithful implementation of it.
          </SectionIntro>
          <ActionRow>
            <Cta href="/docs">
              <span>Read the model</span>
            </Cta>
            <CtaGhost href="https://github.com/nustackdev">
              <GithubMark size={14} />
              <span>GitHub</span>
            </CtaGhost>
          </ActionRow>
        </SectionCol>
        <SectionVisual>
          <VizFrame>
            <OneLineSvg />
          </VizFrame>
        </SectionVisual>
      </SectionSplit>
    </SectionCard>
  );
}
