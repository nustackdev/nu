import { GithubMark } from '@/components/marks/GithubMark';
import {
  ActionRow,
  Cta,
  CtaGhost,
  SectionCard,
  SectionCol,
  SectionIntro,
  SectionTitle,
} from './SectionCard';
import { FABRICS } from './fabrics.data';
import s from './FabricsSection.module.css';

/**
 * §2.5 — the fabrics. Vertical hero rows, hero-scale lowercase names.
 * Each fabric's name takes a distinct display-tuned hue (red, teal,
 * yellow, orange, pink — no green / blue / violet so this section stays
 * chromatically distinct from the site's primary duo). The h3 subtitle
 * stays plain ink so the giant name is the only anchor per row.
 * Reassign colors in FABRIC_NAME_GRAD.
 */
const FABRIC_NAME_GRAD: Record<string, string> = {
  mem: 'gRed',
  virtuals: 'gTeal',
  invisibles: 'gYellow',
  ray: 'gOrange',
  ui: 'gPink',
};
export function FabricsSection() {
  return (
    <SectionCard hue="s2" id="fabrics">
      <SectionCol>
        <SectionTitle>The current fabrics.</SectionTitle>
        <SectionIntro>
          Each <b>Ref</b> resolves inside a <b>fabric</b>. Here are the ones
          Nu speaks today, each a real surface your code writes and reads
          against.
        </SectionIntro>

        <ol className={s.rows}>
          {FABRICS.map((f, i) => {
            const flip = i % 2 === 1;
            const nameGrad =
              s[FABRIC_NAME_GRAD[f.name] ?? 'gBlue'] ?? s.gBlue;
            return (
              <li
                key={f.name}
                className={`${s.row} ${flip ? s.rowFlip : ''}`}
              >
                <div className={s.text}>
                  <span className={`${s.name} ${nameGrad}`}>{f.name}</span>
                  <h3 className={s.rowTitle}>{f.title}</h3>
                  <p className={s.body}>{f.body}</p>
                  {f.backends && (
                    <ul
                      className={s.chips}
                      aria-label={`${f.name} backends`}
                    >
                      {f.backends.map((b) => (
                        <li key={b} className={s.chip}>
                          {b}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div className={s.viz} aria-hidden>
                  <div className={s.vizFrame}>
                    <f.Viz />
                  </div>
                </div>
              </li>
            );
          })}
        </ol>

        <ActionRow>
          <Cta href="/docs">
            <span>Read the fabrics</span>
          </Cta>
          <CtaGhost href="https://github.com/nustackdev">
            <GithubMark size={14} />
            <span>GitHub</span>
          </CtaGhost>
        </ActionRow>
      </SectionCol>
    </SectionCard>
  );
}
