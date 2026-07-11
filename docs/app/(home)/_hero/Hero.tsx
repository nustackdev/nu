import { NustackLogo } from '@/components/marks/NustackLogo';
import { HeroWordmark } from '@/components/marks/HeroWordmark';
import { StackLayersSvg } from '@/components/marks/StackLayers';
import s from './Hero.module.css';

/**
 * Hero — wordmark, claim, mission, then the stack-layers viz frame.
 * The word "nustack" inside <HeroWordmark /> carries the silver→purple gradient.
 */
export function Hero() {
  return (
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
          <b>assembled</b> — from primitives that compose cleanly and hold up
          under real load. The model is called the{' '}
          <span className={s.heroConcept}>interaction model</span>, the
          implementation in Python is <span className={s.heroConcept}>Nu</span>,
          apps compose from it.
        </p>
        <div className={s.heroVizFrame} aria-hidden>
          <StackLayersSvg />
        </div>
      </div>
    </header>
  );
}
