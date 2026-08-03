import Link from 'next/link';
import { ArrowUpRight, BookOpen } from 'lucide-react';
import { GithubMark } from '@/components/marks/GithubMark';
import s from './Hero.module.css';

function XMark({ size = 13 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden
    >
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24h-6.66l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25h6.828l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

const USE_CASES = [
  'Personal apps',
  'Agentic systems',
  'Distributed execution',
  'Enterprise in-house tools',
  'Financial tools',
];

export function Hero() {
  return (
    <header className={s.hero} aria-labelledby="hero-title">
      <div className={s.colLeft}>
        {/* ghost NuLogo — outline, bleeds off left, sits behind text */}
        <svg
          className={s.ghost}
          viewBox="140 144 271 263"
          aria-hidden
          preserveAspectRatio="xMinYMid meet"
        >
          <defs>
            <linearGradient
              id="hero-ghost-grad"
              gradientUnits="userSpaceOnUse"
              x1="1400"
              y1="4080"
              x2="4110"
              y2="1450"
            >
              <stop offset="0.5" stopColor="#7a4ce0" />
              <stop offset="0.5" stopColor="#3e72e7" />
            </linearGradient>
          </defs>
          <g
            transform="translate(0,552) scale(0.1,-0.1)"
            fill="url(#hero-ghost-grad)"
            stroke="none"
          >
            <path d="M2121 4065 c-376 -82 -653 -368 -711 -735 -6 -41 -10 -402 -10 -972 l0 -908 190 0 190 0 0 878 c0 968 -1 941 64 1070 19 37 51 86 71 110 54 62 155 130 238 161 l72 26 363 3 362 3 0 -681 0 -681 143 3 c132 3 145 5 172 26 68 53 64 1 65 900 l0 812 -572 -1 c-449 0 -587 -4 -637 -14z" vectorEffect="non-scaling-stroke" />
            <path d="M3730 3203 c0 -973 2 -940 -66 -1076 -47 -93 -144 -190 -235 -234 -117 -58 -158 -63 -531 -63 l-338 0 0 681 0 680 -142 -3 c-160 -3 -178 -10 -217 -79 -21 -36 -21 -46 -21 -848 l0 -811 563 0 c350 0 586 4 623 11 379 67 675 365 734 739 6 41 10 402 10 973 l0 907 -190 0 -190 0 0 -877z" vectorEffect="non-scaling-stroke" />
          </g>
        </svg>

        <div className={s.stack}>
          <div className={s.line1} aria-hidden>
            <span className={s.wordNu}>Nu</span>
            <span className={s.sep}>&mdash;</span>
          </div>
          <h1 id="hero-title" className={s.slogan}>
            <span className={s.srOnly}>Nu — the interaction primitive.</span>
            <span aria-hidden className={s.sloganLine}>the</span>
            <span aria-hidden className={s.sloganLine}>interaction</span>
            <span aria-hidden className={s.sloganLine}>primitive.</span>
          </h1>
        </div>
      </div>

      <aside className={s.colRight} aria-label="project details">
        <p className={s.tagline}>
          Build apps in one primitive that spans your
          <br />
          whole stack &mdash; databases, UIs, AI agents,
          <br />
          and services. No glue.{' '}
          <em className={s.taglineAccent}>50&times; less code.</em>
        </p>

        <ul className={s.useCasesList}>
          {USE_CASES.map((label) => (
            <li key={label} className={s.useCasesItem}>
              <span>{label}</span>
            </li>
          ))}
        </ul>

        <dl className={s.meta} aria-label="project meta">
          <div className={s.metaRow}>
            <dt className={s.metaKey}>License</dt>
            <dd className={s.metaVal}>Apache&#8209;2.0</dd>
          </div>
          <div className={s.metaRow}>
            <dt className={s.metaKey}>Runtime</dt>
            <dd className={s.metaVal}>Python 3.12+</dd>
          </div>
        </dl>

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
          <a
            className={s.heroCta}
            href="https://twitter.com/nustackdev"
            target="_blank"
            rel="noreferrer"
          >
            <XMark size={13} />
            <span>Follow</span>
            <ArrowUpRight size={13} aria-hidden className={s.heroCtaArrow} />
          </a>
        </div>
      </aside>
    </header>
  );
}
