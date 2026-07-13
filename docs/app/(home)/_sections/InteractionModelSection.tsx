import { BookOpen } from 'lucide-react';
import { GithubMark } from '@/components/marks/GithubMark';
import { OneLineSvg } from '@/components/marks/OneLine';
import {
  ActionRow,
  Cta,
  RepoName,
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
    <SectionCard hue="s1" vizHue="sage" id="interaction-model">
      <SectionSplit>
        <SectionCol>
          <SectionTitle>We build on the interaction model.</SectionTitle>
          <SectionIntro>
            It is a tight programming model with two atoms:
            <br />
            <br />
            <b>Ref</b> - a pointer to any resource (kv key, RPC endpoint,
            UI DOM node, anything).
            <br />
            <b>Interaction</b> - what to do with the resource (read, mutate,
            subscribe, etc).
            <br />
            <br />
            <b>Fabrics</b> are the worlds those addresses resolve inside,
            adapting Refs to real backends.
            <br />
            <br />
            Everything else at nustack is a faithful implementation of it.
          </SectionIntro>
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
