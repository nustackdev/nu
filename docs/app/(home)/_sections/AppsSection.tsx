import { ArrowUpRight } from 'lucide-react';
import { GithubMark } from '@/components/marks/GithubMark';
import {
  SectionCard,
  SectionCol,
  SectionIntro,
  SectionTitle,
} from './SectionCard';
import { APPS } from './apps.data';
import s from './AppsGrid.module.css';

/**
 * §3 — apps built on Nu.
 * Same rhythm as FabricsSection: alternating vertical rows, silver-woven
 * hero name per app, GitHub repo button in the action row, and a mock
 * screenshot in the viz frame that auto-recolors from the row's hue tokens.
 */
export function AppsSection() {
  return (
    <SectionCard hue="s3" id="apps">
      <SectionCol>
        <SectionTitle>Standalone apps built on Nu.</SectionTitle>
        <SectionIntro>
          The tools we ship for others. They share Nu&apos;s shape and
          language — you learn one, you know them all.
        </SectionIntro>

        <ol className={s.rows}>
          {APPS.map((a, i) => {
            const flip = i % 2 === 1;
            return (
              <li
                key={a.name}
                data-app={a.name}
                className={`${s.row} ${flip ? s.rowFlip : ''}`}
              >
                <div className={s.text}>
                  <span className={s.name}>{a.name}</span>
                  <h3 className={s.rowTitle}>{a.title}</h3>
                  <p className={s.body}>{a.body}</p>
                  <div className={s.actions}>
                    <a
                      className={s.repoBtn}
                      href={a.repo}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <GithubMark size={14} />
                      <span>{a.repo.replace('https://github.com/', '')}</span>
                      <ArrowUpRight size={13} aria-hidden className={s.repoArrow} />
                    </a>
                  </div>
                </div>
                <div className={s.viz} aria-hidden>
                  <div className={s.vizFrame}>
                    <a.Viz />
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      </SectionCol>
    </SectionCard>
  );
}
