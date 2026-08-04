import { BookOpen } from 'lucide-react';
import { GithubMark } from '@/components/site/marks/GithubMark';
import { SiteButton, SiteButtonRepoLabel } from '@/components/site/SiteButton';
import {
  ActionRow,
  SectionCard,
  SectionCol,
  SectionIntro,
  SectionTitle,
} from './SectionCard';
import { NuCodeSample } from './NuCodeSample';

/**
 * §2 — Nu, the implementation.
 * Vertical stack: title + intro up top, IDE-style code block full-width
 * below, actions at the bottom.
 */
export function NuSection() {
  return (
    <SectionCard hue="s2" vizHue="teal" id="nu">
      <SectionCol>
        <SectionTitle>Nu - the interaction model made real in Python.</SectionTitle>
        <SectionIntro>
          Nu ships the model in pure Python. Batteries included:{' '}
          <b>fabrics</b> for the everyday jobs - in-memory state, kv-based
          state, Ray-distributed compute, UI building.
        </SectionIntro>
        <NuCodeSample />
        <ActionRow>
          <SiteButton href="/docs">
            <BookOpen size={14} aria-hidden />
            <span>Meet Nu</span>
          </SiteButton>
          <SiteButton href="https://github.com/nustackdev/nu">
            <GithubMark size={14} />
            <SiteButtonRepoLabel>nustackdev/nu</SiteButtonRepoLabel>
          </SiteButton>
          <SiteButton href="https://github.com/nustackdev/nu/tree/main/examples">
            <GithubMark size={14} />
            <span>See more examples</span>
          </SiteButton>
        </ActionRow>
      </SectionCol>
    </SectionCard>
  );
}
