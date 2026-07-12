import Link from 'next/link';
import { ArrowUpRight } from 'lucide-react';
import { NustackLogo } from '@/components/marks/NustackLogo';
import { HeroWordmark } from '@/components/marks/HeroWordmark';
import { HeroViz } from './HeroViz';
import s from './Hero.module.css';

const TRAITS = [
  'distributed',
  'persistent',
  'reactive',
  'reload-proof',
  'inspectable',
  'traceable',
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
            <span className={s.labelKey}>license</span>
            <span className={s.labelVal}>Apache-2.0</span>
          </span>
          <span className={s.label}>
            <span className={s.labelKey}>python</span>
            <span className={s.labelVal}>3.12+</span>
          </span>
        </div>

        <p className={s.heroMission}>
          Assemble software that is{' '}
          {TRAITS.map((t, i) => (
            <span key={t}>
              <b>{t}</b>
              {i < TRAITS.length - 1 ? ', ' : ' '}
            </span>
          ))}
          <span className={s.heroMissionSep}>—</span> 50× easier than writing
          it line by line in imperative Python.
        </p>

        <div className={s.heroCtaRow}>
          <a
            className={s.heroCta}
            href="https://github.com/nustackdev/interaction-model"
            target="_blank"
            rel="noreferrer"
          >
            <span>Interaction model</span>
            <ArrowUpRight size={13} aria-hidden className={s.heroCtaArrow} />
          </a>
          <a
            className={s.heroCta}
            href="https://github.com/nustackdev/nu"
            target="_blank"
            rel="noreferrer"
          >
            <span>Nu repo</span>
            <ArrowUpRight size={13} aria-hidden className={s.heroCtaArrow} />
          </a>
          <Link className={s.heroCta} href="/docs">
            <span>Nu docs</span>
            <ArrowUpRight size={13} aria-hidden className={s.heroCtaArrow} />
          </Link>
        </div>

        <HeroViz />
      </div>
    </header>
  );
}
