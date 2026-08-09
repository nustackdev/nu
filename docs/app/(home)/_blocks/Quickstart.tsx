import { BookOpen } from 'lucide-react';
import { Description } from '@/components/site/text';
import { CodeSample } from '@/components/site/CodeSample';
import { CtaRow } from '@/components/site/layout/CtaRow';
import { SiteButton } from '@/components/site/SiteButton';
import { GithubMark } from '@/components/site/marks/GithubMark';
import { Chapter, Section, SectionHead } from '@/components/site/page';
import { QUICKSTART_TERMINAL_LINES } from '../intro.sample.data';
import s from './Quickstart.module.css';

/**
 * Quickstart — single terminal session that mirrors the README quickstart:
 * install, run the bundled demo, open the browser tab. Left column carries
 * the framing + prerequisite + follow-up links; right column is the shell.
 */
export function Quickstart() {
  return (
    <Chapter>
      <SectionHead
        title="Quickstart."
        lede={<>Three commands to a live counter on a browser dashboard, persisted across restarts.</>}
      />

      <Section>
        <div className={s.wrap}>
          <div className={s.left}>
            <Description>
              Requires Python 3.10+. Everything else comes with the
              wheel &mdash; RocksDB, the UI server, the CLI.
            </Description>
            <Description>
              <code>nu demo</code> shows all bundled demos.
            </Description>
            <CtaRow>
              <SiteButton href="/docs" variant="hueTinted">
                <BookOpen size={14} aria-hidden />
                <span>Docs</span>
              </SiteButton>
              <SiteButton href="https://github.com/nustackdev/nu/tree/main/examples">
                <GithubMark size={14} />
                <span>Check out examples</span>
              </SiteButton>
            </CtaRow>
          </div>
          <div className={`${s.right} ${s.codeScope}`}>
            <CodeSample
              filename="terminal"
              lang="bash"
              langShort="sh"
              lines={QUICKSTART_TERMINAL_LINES}
            />
          </div>
        </div>
      </Section>
    </Chapter>
  );
}
