import Link from 'next/link';
import type { ComponentType } from 'react';
import { ArrowRight } from 'lucide-react';
import { GithubMark } from '@/components/marks/GithubMark';
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

        {/* ---------- §1 interaction model — text LEFT, visual RIGHT. ---------- */}
        <section className={s.section} id="interaction-model" data-hue="s1">
          <div className={s.sectionCard}>
            <div className={s.sectionSplit}>
              <div className={s.sectionCol}>
                <h2 className={s.sectionTitle}>We build on the interaction model.</h2>
                <p className={s.sectionIntro}>
                  A tiny theory of computation: <b>Refs</b> address values,{' '}
                  <b>Interactions</b> change them, <b>Fabrics</b> are the worlds
                  those addresses resolve inside. Everything else at{' '}
                  <NustackMark /> is a faithful implementation of it.
                </p>
                <div className={s.modelActions}>
                  <Link href="/interaction-model" className={s.cta}>
                    <span>read the model</span>
                    <ArrowRight size={13} aria-hidden className={s.ctaArrow} />
                  </Link>
                  <a
                    href="https://github.com/nustackdev"
                    target="_blank"
                    rel="noreferrer"
                    className={s.ctaGhost}
                  >
                    <GithubMark size={14} />
                    <span>github</span>
                  </a>
                </div>
              </div>
              <aside className={s.sectionVisual} data-slot="interaction-model">
                <div className={s.vizFrame}>
                  <OneLineSvg />
                </div>
              </aside>
            </div>
          </div>
        </section>

        {/* ---------- §2 Nu — code LEFT, text RIGHT. ---------- */}
        <section className={s.section} id="nu" data-hue="s2">
          <div className={s.sectionCard}>
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
              <h2 className={s.sectionTitle}>Nu — the interaction model, made real.</h2>
              <p className={s.sectionIntro}>
                Nu ships the model in pure Python and grows it into a small
                stack of <b>fabrics</b> ({FABRICS.join(' · ')}) — everything
                else we make stands on this.
              </p>
              <div className={s.modelActions}>
                <Link href="/nu" className={s.cta}>
                  <span>meet Nu</span>
                  <ArrowRight size={13} aria-hidden className={s.ctaArrow} />
                </Link>
                <a
                  href="https://github.com/nustackdev/nu"
                  target="_blank"
                  rel="noreferrer"
                  className={s.ctaGhost}
                >
                  <GithubMark size={14} />
                  <span>github</span>
                </a>
              </div>
            </div>
            </div>
          </div>
        </section>

        {/* ---------- §3 apps — text LEFT, shelf RIGHT, app grid below. ---------- */}
        <section className={s.section} id="apps" data-hue="s3">
          <div className={s.sectionCard}>
            <div className={s.sectionSplit}>
              <div className={s.sectionCol}>
                <h2 className={s.sectionTitle}>Standalone apps built on Nu.</h2>
                <p className={s.sectionIntro}>
                  The tools we ship for others. They share Nu&apos;s shape and
                  language — you learn one, you know them all.
                </p>
                <div className={s.modelActions}>
                  <Link href="#apps-grid" className={s.cta}>
                    <span>browse apps</span>
                    <ArrowRight size={13} aria-hidden className={s.ctaArrow} />
                  </Link>
                  <a
                    href="https://github.com/nustackdev"
                    target="_blank"
                    rel="noreferrer"
                    className={s.ctaGhost}
                  >
                    <GithubMark size={14} />
                    <span>github</span>
                  </a>
                </div>
              </div>
              <aside className={s.sectionVisual} aria-hidden>
                <div className={s.vizFrame}>
                  <div className={s.sectionShelf}>
                    <AppShelfSvg />
                  </div>
                </div>
              </aside>
            </div>
            <div id="apps-grid" className={s.flatGrid}>
              {APPS.map((a) => (
                <Link key={a.name} href={a.href} className={s.flatCell}>
                  <div className={s.flatCellViz} aria-hidden>
                    <a.Viz />
                  </div>
                  <span className={s.flatCellName}>{a.name}</span>
                  <h3 className={s.flatCellTitle}>{a.title}</h3>
                  <p className={s.flatCellBody}>{a.body}</p>
                  <span className={s.flatArrow}>
                    <span>open</span>
                    <ArrowRight size={12} aria-hidden />
                  </span>
                </Link>
              ))}
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
