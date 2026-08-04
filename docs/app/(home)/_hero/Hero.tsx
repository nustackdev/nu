import Link from 'next/link';
import { ArrowUpRight, BookOpen } from 'lucide-react';
import { GithubMark } from '@/components/site/marks/GithubMark';
import { NuLogo } from '@/components/site/marks/NuLogo';
import s from './Hero.module.css';

function XMark({ size = 13 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24h-6.66l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25h6.828l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

function DiscordMark({ size = 14 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M20.317 4.492a19.79 19.79 0 0 0-4.885-1.515.074.074 0 0 0-.079.036c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.036A19.736 19.736 0 0 0 3.677 4.492a.07.07 0 0 0-.032.027C.533 9.093-.32 13.555.099 17.961a.082.082 0 0 0 .031.056 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128c.126-.094.252-.192.372-.291a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.009c.12.099.246.198.373.292a.077.077 0 0 1-.006.128 12.299 12.299 0 0 1-1.873.891.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.055c.5-5.094-.838-9.52-3.549-13.442a.061.061 0 0 0-.031-.028zM8.02 15.278c-1.182 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
    </svg>
  );
}

const USE_CASES = [
  'AI agentic systems',
  'Personal apps',
  'Data-intensive apps',
  'Enterprise in-house tools',
  'Observability dashboards',
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

        <h1 id="hero-title" className={`${s.stack} ${s.slogan}`}>
          <span className={s.srOnly}>Nu — the interaction primitive.</span>
          <span aria-hidden className={`${s.sloganLine} ${s.desktopOnly}`}>Nu &mdash;</span>
          <span aria-hidden className={`${s.sloganLine} ${s.desktopOnly}`}>the</span>
          <span aria-hidden className={`${s.sloganLine} ${s.desktopOnly}`}>interaction</span>
          <span aria-hidden className={`${s.sloganLine} ${s.desktopOnly}`}>primitive.</span>

          <span aria-hidden className={s.mobileTitle}>
            <NuLogo className={s.inlineLogo} />
            <span>Nu &mdash; the interaction primitive.</span>
          </span>
        </h1>
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

        <p className={s.useCasesKicker}>Built for</p>
        <ol className={s.useCasesList}>
          {USE_CASES.map((label, i) => (
            <li key={label} className={s.useCasesItem}>
              <span className={s.useCasesNum}>{String(i + 1).padStart(2, '0')}</span>
              <span>{label}</span>
            </li>
          ))}
        </ol>

        <div className={s.heroCtaRow}>
          <Link className={`${s.heroCta} ${s.heroCtaPurple}`} href="/docs">
            <BookOpen size={14} aria-hidden />
            <span>Quickstart</span>
            <ArrowUpRight size={13} aria-hidden className={s.heroCtaArrow} />
          </Link>
          <a
            className={`${s.heroCta} ${s.heroCtaBlue}`}
            href="https://github.com/nustackdev/nu"
            target="_blank"
            rel="noreferrer"
          >
            <GithubMark size={14} />
            <span className={s.heroCtaRepo}>nustackdev/nu</span>
            <ArrowUpRight size={13} aria-hidden className={s.heroCtaArrow} />
          </a>
        </div>
        <div className={s.heroCtaRow}>
          <a
            className={s.heroCta}
            href="https://discord.gg/tCa8YE7XVr"
            target="_blank"
            rel="noreferrer"
          >
            <DiscordMark size={14} />
            <span>Discord</span>
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

        <p className={s.metaLine} aria-label="project meta">
          Apache&#8209;2.0 <span>·</span> Python 3.12+
        </p>
      </aside>
    </header>
  );
}
