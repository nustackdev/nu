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
 * §2.5 — the fabrics. Vertical hero rows with silver-woven names: each
 * fabric's giant name is a silver → hue gradient with ONE low-saturation
 * endpoint. The same hue propagates to the row's backend chips and the
 * glyph via row-scoped --nu-accent[-2] overrides in FabricsSection.module.css
 * — FabricGlyphs reads those tokens directly, so no glyph duplication.
 *
 * Vibe: metallic + editorial. Color is a whisper, silver carries the row.
 */
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
            return (
              <li
                key={f.name}
                data-fabric={f.name}
                className={`${s.row} ${flip ? s.rowFlip : ''}`}
              >
                <div className={s.text}>
                  <span className={s.name}>nu.{f.name}</span>
                  <h3 className={s.rowTitle}>{f.title}</h3>
                  <p className={s.body}>{f.body}</p>
                  {f.backends && (
                    <ul
                      className={s.chips}
                      aria-label={`nu.${f.name} backends`}
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
