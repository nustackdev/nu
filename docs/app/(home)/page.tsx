import Link from 'next/link';
import type { ComponentType } from 'react';
import { ArrowRight } from 'lucide-react';
import { NustackMark } from '@/components/marks/NustackMark';
import { NustackLogo } from '@/components/marks/NustackLogo';
import { HeroWordmark } from '@/components/marks/HeroWordmark';
import { OneLineSvg } from '@/components/marks/variations/interaction/one-line';
import { StackLayersSvg } from '@/components/marks/variations/apps/stack-layers';
import { AppShelfSvg } from '@/components/marks/variations/apps/app-shelf';
import { NulogMockSvg } from '@/components/marks/variations/apps/nulog-mock';
import { NuspaceMockSvg } from '@/components/marks/NuspaceMock';
import s from './nustack.module.css';

type App = {
  name: string;
  title: string;
  body: string;
  href: string;
  Viz: ComponentType;
};

const APPS: App[] = [
  {
    name: 'nulog',
    title: 'Logging built on Nu shapes.',
    body: 'Structured logs as first-class Refs. One shape end-to-end — capture, query, ship.',
    href: '/nulog',
    Viz: NulogMockSvg,
  },
  {
    name: 'nuspace',
    title: 'A workspace for building on Nu.',
    body: 'Apps, tabs, and data live under one roof. Nudle-native. Composable, inspectable.',
    href: '/nuspace',
    Viz: NuspaceMockSvg,
  },
];

const FABRICS = ['shapes', 'mem', 'nudle', 'apps', 'lens'];

export default function HomePage() {
  return (
    <div className={s.root}>
      {/* Hero JB gradient plane — three stacked radials at 50% 22%. Verbatim. */}
      <div className={s.heroBg} aria-hidden />

      {/* PAGE BG — reserved layer for any future page-wide overlay. Empty
          today; the hero JB gradient plane above carries all the color. */}
      <div className={s.pageBg} aria-hidden />

      {/* Full-page dot grain — fixed layer over EVERYTHING. */}
      <div className={s.grain} aria-hidden />

      <div className={s.shell}>

        {/* ---------- hero: single-column, wordmark-led ---------- */}
        <header className={s.hero}>
          <div className={s.heroInner}>
            <div className={s.heroWordmark}>
              <NustackLogo size="0.92em" className={s.heroWordmarkLogo} />
              <HeroWordmark />
            </div>
            <h1 className={s.heroClaim}>
              <b>assemble</b> software, not write it.
            </h1>
            <p className={s.heroMission}>
              Systems today are written line by line. We think they should be{' '}
              <b>assembled</b> — from primitives that compose cleanly and
              hold up under real load. The model is called the{' '}
              <span className={s.heroConcept}>interaction model</span>, the
              implementation in Python is <span className={s.heroConcept}>Nu</span>,
              apps compose from it.
            </p>
            <div className={s.heroVizFrame} aria-hidden>
              <StackLayersSvg />
            </div>
          </div>
        </header>

        {/* ---------- §1 interaction model — bloom RIGHT (blue).
                       Content sits on the LEFT column (darker side). ---------- */}
        <section className={s.section} id="interaction-model" data-hue="s1">
<div className={s.sectionSplit}>
            <div className={s.sectionCol}>
              <div className={s.sectionLabel}>the model</div>
              <h2 className={s.sectionTitle}>We build on the interaction model.</h2>
              <p className={s.sectionIntro}>
                A tiny theory of computation: <b>Refs</b> address values,{' '}
                <b>Interactions</b> change them, <b>Fabrics</b> are the worlds
                those addresses resolve inside. Everything else at{' '}
                <NustackMark /> is a faithful implementation of it.
              </p>
              <div className={s.modelActions}>
                <Link href="/interaction-model" className={s.heroCtaGhost}>
                  <span>read the model</span>
                  <ArrowRight size={13} aria-hidden />
                </Link>
              </div>
            </div>
            <aside className={s.sectionVisual} data-slot="interaction-model">
              <div className={s.glassCard}>
                <OneLineSvg />
              </div>
            </aside>
          </div>
        </section>

        {/* ---------- §2 Nu — bloom LEFT (teal).
                       Content sits on the RIGHT column (darker side). ---------- */}
        <section className={s.section} id="nu" data-hue="s2">
          <div className={`${s.sectionSplit} ${s.sectionSplitFlip}`}>
            <aside className={s.sectionVisual}>
              <div className={s.codeShell}>
                <pre className={s.codeBlock}>
<span className={s.cmt}>{'"""Basic Nu bracket-tree app: mem preset + tiny compute."""'}</span>
{'\n\n'}
<span className={s.kw}>from</span>{' __future__ '}<span className={s.kw}>import</span>{' annotations\n\n'}
<span className={s.kw}>import</span>{' '}<span className={s.nu}>nu</span>{'\n\n\n'}
<span className={s.kw}>class</span>{' Counter('}<span className={s.nu}>nu.Shape</span>{'):\n    value: '}<span className={s.nu}>nu.v.IntRef</span>{'\n\n\n'}
{'tree = '}<span className={s.nu}>nu.With</span>{'(\n    '}<span className={s.nu}>nu.v.presets.memory_navigator</span>{'(),\n    body='}<span className={s.nu}>nu.v.Transaction</span>{'(Counter.value.store(0) >> Counter.value.store(Counter.value + 42))\n    >> '}<span className={s.nu}>nu.v.Snapshot</span>{'('}<span className={s.nu}>nu.print</span>{'(Counter.value)),\n)\n\n\n'}
<span className={s.kw}>if</span>{' __name__ == '}<span className={s.str}>{"'__main__'"}</span>{':\n    '}<span className={s.nu}>nu.run</span>{'(tree)\n'}
                </pre>
                <div className={s.codeCaption}>examples/basic.py · 20 loc</div>
              </div>
            </aside>
            <div className={s.sectionCol}>
              <div className={s.sectionLabel}>the platform</div>
              <h2 className={s.sectionTitle}>Nu — the interaction model, made real.</h2>
              <p className={s.sectionIntro}>
                Nu ships the model in pure Python and grows it into a small
                stack of <b>fabrics</b> ({FABRICS.join(' · ')}) — everything
                else we make stands on this.
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
            </div>
          </div>
        </section>

        {/* ---------- §3 apps — bloom BOTTOM-LEFT (magenta).
                       Content sits at TOP (darker side). ---------- */}
        <section className={s.section} id="apps" data-hue="s3">
          <div className={s.sectionCol}>
            <div className={s.sectionLabel}>apps</div>
            <h2 className={s.sectionTitle}>Standalone apps built on Nu.</h2>
            <p className={s.sectionIntro}>
              The tools we ship for others. They share Nu&apos;s shape and
              language — you learn one, you know them all.
            </p>
          </div>
          <div className={s.sectionShelf} aria-hidden>
            <AppShelfSvg />
          </div>
          <div className={`${s.flatGrid} ${s.flatGridCols3}`}>
            {APPS.map((a) => (
              <Link key={a.name} href={a.href} className={s.flatCell}>
                <div className={s.flatCellViz} aria-hidden>
                  <a.Viz />
                </div>
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

        {/* ---------- footer — bloom TOP-CENTER, low-intensity (bright blue).
                       Soft close, fades into black. ---------- */}
        <footer className={s.footer} data-hue="s4">
          <div className={s.footerCell}>
            <span className={s.footerCellHead}>org</span>
            <span className={s.footerBrand}>
              <NustackMark />
            </span>
            <span className={s.footerCellBody}>
              <NustackMark /> © 2026
            </span>
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
