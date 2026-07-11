import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { GithubMark } from '@/components/marks/GithubMark';
import { AppShelfSvg } from '@/components/marks/AppShelf';
import {
  ActionRow,
  Cta,
  CtaGhost,
  SectionCard,
  SectionCol,
  SectionIntro,
  SectionSplit,
  SectionTitle,
  SectionVisual,
  VizFrame,
  sectionShelfClass,
} from './SectionCard';
import { APPS } from './apps.data';
import s from './AppsGrid.module.css';

/**
 * §3 — apps built on Nu.
 * Header split (text-left + shelf-right) with a 2-tile app grid below.
 * Blue hue (s3).
 */
export function AppsSection() {
  return (
    <SectionCard hue="s3" id="apps">
      <SectionSplit>
        <SectionCol>
          <SectionTitle>Standalone apps built on Nu.</SectionTitle>
          <SectionIntro>
            The tools we ship for others. They share Nu&apos;s shape and
            language — you learn one, you know them all.
          </SectionIntro>
          <ActionRow>
            <Cta href="#apps-grid">
              <span>browse apps</span>
            </Cta>
            <CtaGhost href="https://github.com/nustackdev">
              <GithubMark size={14} />
              <span>github</span>
            </CtaGhost>
          </ActionRow>
        </SectionCol>
        <SectionVisual aria-hidden>
          <VizFrame>
            <div className={sectionShelfClass}>
              <AppShelfSvg />
            </div>
          </VizFrame>
        </SectionVisual>
      </SectionSplit>

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
    </SectionCard>
  );
}
