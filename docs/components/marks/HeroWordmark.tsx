import styles from './HeroWordmark.module.css';

/**
 * Display-scale wordmark for the hero — gradient-clipped, layered.
 * The `NU` reads as a violet aurora; `STACK` is a subtle ink metallic.
 * Meant to be dropped inside a container that sets its font-size.
 */
export function HeroWordmark() {
  return (
    <span className={styles.mark} aria-label="NUSTACK">
      <span className={styles.nu} aria-hidden>NU</span>
      <span className={styles.stack} aria-hidden>STACK</span>
    </span>
  );
}
