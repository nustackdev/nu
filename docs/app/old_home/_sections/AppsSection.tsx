import { GithubMark } from '@/components/site/marks/GithubMark';
import { SiteButton } from '@/components/site/SiteButton';
import { SilverWovenName, type SilverWovenHue } from '@/components/site/SilverWovenName';
import { VizFrame } from '@/components/site/VizFrame';
import {
  SectionCard,
  SectionCol,
  SectionIntro,
  SectionTitle,
} from './SectionCard';
import { APPS } from './apps.data';
import s from './AppsGrid.module.css';

/** Map app name → silver-woven hue key. */
const APP_HUE: Record<string, SilverWovenHue> = {
  nulog: 'amber',
  nuspace: 'plum',
};

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
          Applications built on Nu today.
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
                  <SilverWovenName hue={APP_HUE[a.name]}>{a.name}</SilverWovenName>
                  <h3 className={s.rowTitle}>{a.title}</h3>
                  <p className={s.body}>{a.body}</p>
                  <div className={s.actions}>
                    {a.comingSoon ? (
                      <SiteButton variant="ghost">Coming soon</SiteButton>
                    ) : (
                      a.repo && (
                        <SiteButton variant="repo" href={a.repo}>
                          <GithubMark size={14} />
                          <span>{a.repo.replace('https://github.com/', '')}</span>
                        </SiteButton>
                      )
                    )}
                  </div>
                </div>
                <div className={s.viz} aria-hidden>
                  <VizFrame>
                    <a.Viz />
                  </VizFrame>
                </div>
              </li>
            );
          })}
        </ol>
      </SectionCol>
    </SectionCard>
  );
}
