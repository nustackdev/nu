import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { GithubMark } from '@/components/marks/GithubMark';
import s from './nustack.module.css';

type App = {
  name: string;
  title: string;
  body: string;
  href: string;
};

const APPS: App[] = [
  {
    name: 'nulog',
    title: 'Logging built on Nu shapes.',
    body: 'Structured logs as first-class Refs. One shape end-to-end — capture, query, ship.',
    href: '/nulog',
  },
  {
    name: 'nuspace',
    title: 'A workspace for building on Nu.',
    body: 'Apps, tabs, and data live under one roof. Nudle-native. Composable, inspectable.',
    href: '/nuspace',
  },
];

const FABRICS = ['shapes', 'mem', 'nudle', 'apps', 'lens'];

export default function HomePage() {
  return (
    <div className={s.root}>
      <div className={s.shell}>

        {/* ---------- hero: manifest, typography-driven ---------- */}
        <header className={s.hero}>
          <div className={s.heroGrid} aria-hidden />
          <div className={s.heroGlow} aria-hidden />

          <div className={s.heroBody}>
            <div className={s.heroEyebrow}>
              <span>todo — iterate copy soon</span>
              <span className={s.heroCaret} aria-hidden />
            </div>
            <h1 className={s.heroClaim}>
              Rebuilding the <b>ground layer</b> of software.
            </h1>
            <p className={s.heroMission}>
              Systems today are written line by line. We think they should be{' '}
              <b>assembled</b> — from a small, honest set of pieces that
              compose cleanly and hold up under real load. That work lives in
              Nu, and in every product, tool, and fabric that grows on top of
              it.
            </p>
            <div className={s.heroActions}>
              <Link href="/nu" className={s.heroCta}>
                <span>meet Nu</span>
                <ArrowRight size={14} className={s.heroCtaArrow} aria-hidden />
              </Link>
              <a
                href="https://github.com/nustackdev"
                className={s.heroCtaGhost}
              >
                <GithubMark size={13} />
                <span>github.com/nustackdev</span>
              </a>
            </div>
          </div>
        </header>

        {/* ---------- interaction model ---------- */}
        <section className={s.section} id="interaction-model">
          <div className={s.sectionLabel}>the model</div>
          <h2 className={s.sectionTitle}>We build on the interaction model.</h2>
          <p className={s.sectionIntro}>
            A tiny theory of computation: <b>Refs</b> address values,{' '}
            <b>Interactions</b> change them, <b>Fabrics</b> are the worlds
            those addresses resolve inside. Everything else at nustack is a
            faithful implementation of it.
          </p>
          <div className={s.modelActions}>
            <Link href="/interaction-model" className={s.heroCtaGhost}>
              <span>read the model</span>
              <ArrowRight size={13} aria-hidden />
            </Link>
          </div>
        </section>

        {/* ---------- Nu — implementation of the model ---------- */}
        <section className={s.section} id="nu">
          <div className={s.sectionLabel}>the platform</div>
          <h2 className={s.sectionTitle}>Nu — the interaction model, made real.</h2>
          <p className={s.sectionIntro}>
            Nu is our main tool. It ships the model in pure Python and grows
            it into a small stack of <b>fabrics</b> ({FABRICS.join(' · ')}){' '}
            — everything else we make stands on this.
          </p>
          <div className={s.modelActions}>
            <Link href="/nu" className={s.heroCtaGhost}>
              <span>meet Nu</span>
              <ArrowRight size={13} aria-hidden />
            </Link>
            <Link href="/docs" className={s.heroCtaGhost}>
              <span>the docs</span>
              <ArrowRight size={13} aria-hidden />
            </Link>
          </div>
        </section>

        {/* ---------- apps ---------- */}
        <section className={s.section} id="apps">
          <div className={s.sectionLabel}>apps</div>
          <h2 className={s.sectionTitle}>Standalone apps built on Nu.</h2>
          <p className={s.sectionIntro}>
            The tools we ship for others. They share Nu&apos;s shape and
            language — you learn one, you know them all.
          </p>
          <div className={`${s.flatGrid} ${s.flatGridCols3}`}>
            {APPS.map((a) => (
              <Link key={a.name} href={a.href} className={s.flatCell}>
                <span className={`${s.flatStatus} ${s.flatStatusLive}`}>live</span>
                <span className={s.flatCellName}>{a.name}</span>
                <h3 className={s.flatCellTitle}>{a.title}</h3>
                <p className={s.flatCellBody}>{a.body}</p>
                <span className={s.flatArrow}>
                  <span>open</span>
                  <ArrowRight size={12} aria-hidden />
                </span>
              </Link>
            ))}
            <div className={`${s.flatCell} ${s.flatCellSoon}`}>
              <span className={s.flatStatus}>tbd</span>
              <span className={s.flatCellName}>more</span>
              <h3 className={s.flatCellTitle}>More to come.</h3>
              <p className={s.flatCellBody}>
                We keep the list honest — new apps land here when they ship,
                not before.
              </p>
              <span className={s.flatArrowSoon}>—</span>
            </div>
          </div>
        </section>

        {/* ---------- footer ---------- */}
        <footer className={s.footer}>
          <div className={s.footerCell}>
            <span className={s.footerCellHead}>org</span>
            <span className={s.footerBrand}>
              nu<em>stack</em>
            </span>
            <span className={s.footerCellBody}>nustack © 2026</span>
          </div>
          <div className={s.footerCell}>
            <span className={s.footerCellHead}>explore</span>
            <span className={s.footerCellBody}>
              <a href="#interaction-model">the model</a>
            </span>
            <span className={s.footerCellBody}>
              <Link href="/nu">Nu</Link>
            </span>
            <span className={s.footerCellBody}>
              <a href="#apps">apps</a>
            </span>
          </div>
          <div className={s.footerCell}>
            <span className={s.footerCellHead}>elsewhere</span>
            <span className={s.footerCellBody}>
              <a href="https://github.com/nustackdev">github</a>
            </span>
            <span className={s.footerCellBody}>
              <Link href="/docs">docs</Link>
            </span>
          </div>
        </footer>

      </div>
    </div>
  );
}
