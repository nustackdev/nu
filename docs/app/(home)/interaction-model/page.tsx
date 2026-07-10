import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { NustackMark } from '@/components/marks/NustackMark';
import s from '../nustack.module.css';

export default function InteractionModelPage() {
  return (
    <div className={s.root}>
      <div className={s.shell}>

        <header className={s.hero}>
          <div className={s.heroGrid} aria-hidden />
          <div className={s.heroGlow} aria-hidden />

          <div className={s.heroInner}>
            <div className={s.heroBody}>
              <div className={s.heroEyebrow}>
                <span>the model · draft · wip</span>
              </div>
              <h1 className={s.heroClaim}>
                The <b>interaction model</b>.
              </h1>
              <p className={s.heroMission}>
                A small theory of computation — Refs, Interactions, Fabrics — and
                a way to compose them. This page will hold the full write-up.
                For now, it&apos;s a stub. The material lives in{' '}
                <code>nu/model/</code> and will be compiled here.
              </p>
            </div>
            <div className={s.heroAside}>
              <Link href="/" className={s.heroCtaGhost}>
                <span>back to <NustackMark /></span>
                <ArrowRight size={13} aria-hidden />
              </Link>
              <Link href="/nu" className={s.heroCtaGhost}>
                <span>meet Nu</span>
                <ArrowRight size={13} aria-hidden />
              </Link>
            </div>
          </div>
        </header>

      </div>
    </div>
  );
}
