import Link from 'next/link';
import { ArrowUpRight, BookOpen } from 'lucide-react';
import { NustackLogo } from '@/components/marks/NustackLogo';
import { HeroWordmark } from '@/components/marks/HeroWordmark';
import { GithubMark } from '@/components/marks/GithubMark';
import { HeroViz } from './HeroViz';
import s from './Hero.module.css';

const TRAITS = [
  'distributed',
  'persistent',
  'reactive',
  'reload-proof',
  'inspectable',
];

/**
 * Hero — wordmark, claim, GitHub-style meta labels, mission, two audience
 * cards (agents / humans), primary CTAs.
 * The word "nustack" inside <HeroWordmark /> carries the silver→purple gradient.
 */
export function Hero() {
  return (
    <header className={s.hero}>
      <div className={s.heroInner}>
        <div className={s.heroWordmark}>
          <NustackLogo className={s.heroWordmarkLogo} />
          <HeroWordmark />
        </div>

        <h1 className={s.heroClaim}>
          Assemble software, don&apos;t write it.
        </h1>

        <div className={s.heroLabels} aria-label="project meta">
          <span className={s.label}>
            <span className={s.labelKey}>open-source</span>
            <span className={s.labelVal}>Apache-2.0</span>
          </span>
          <span className={s.label}>
            <span className={s.labelKey}>python</span>
            <span className={s.labelVal}>3.12+</span>
          </span>
        </div>

        <div className={s.heroMissionGroup}>
          <p className={s.heroMission}>
            Assemble software that is{' '}
            {TRAITS.map((t, i) => (
              <span key={t}>
                <b>{t}</b>
                {i < TRAITS.length - 1 ? ', ' : '.'}
              </span>
            ))}
          </p>
          <p className={s.heroMission}>
            <span className={s.heroMissionAccent}>50x less code</span> for
            humans, <span className={s.heroMissionAccent2}>50x less tokens</span>{' '}
            for agents than writing it line by line in imperative Python.
          </p>
        </div>

        <div className={s.heroCtaRow}>
          <Link className={s.heroCta} href="/docs">
            <BookOpen size={14} aria-hidden />
            <span>Nu docs</span>
            <ArrowUpRight size={13} aria-hidden className={s.heroCtaArrow} />
          </Link>
          <a
            className={s.heroCta}
            href="https://github.com/nustackdev/nu"
            target="_blank"
            rel="noreferrer"
          >
            <GithubMark size={14} />
            <span className={s.heroCtaRepo}>nustackdev/nu</span>
            <ArrowUpRight size={13} aria-hidden className={s.heroCtaArrow} />
          </a>
        </div>

        <HeroViz />
      </div>
    </header>
  );
}
