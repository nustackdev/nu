import { BookOpen } from 'lucide-react';
import { GithubMark } from '@/components/marks/GithubMark';
import {
  ActionRow,
  Cta,
  RepoName,
  SectionCard,
  SectionCol,
  SectionIntro,
  SectionTitle,
} from './SectionCard';
import { NuCodeSample } from './NuCodeSample';

const FABRICS = ['shapes', 'mem', 'nudle', 'apps', 'lens'];

/**
 * §2 — Nu, the implementation.
 * Vertical stack: title + intro up top, IDE-style code block full-width
 * below, actions at the bottom.
 */
export function NuSection() {
  return (
    <SectionCard hue="s2" id="nu">
      <SectionCol>
        <SectionTitle>Nu, the interaction model made real.</SectionTitle>
        <SectionIntro>
          Nu ships the model in pure Python and grows it into a small stack of{' '}
          <b>fabrics</b> ({FABRICS.join(' · ')}), everything else we make stands
          on this.
        </SectionIntro>
        <NuCodeSample />
        <ActionRow>
          <Cta href="/docs">
            <BookOpen size={14} aria-hidden />
            <span>Meet Nu</span>
          </Cta>
          <Cta href="https://github.com/nustackdev/nu">
            <GithubMark size={14} />
            <RepoName>nustackdev/nu</RepoName>
          </Cta>
        </ActionRow>
      </SectionCol>
    </SectionCard>
  );
}
