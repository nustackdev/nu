import styles from './HeroWordmark.module.css';

/**
 * Display-scale wordmark for the hero — gradient-clipped, layered.
 * The `nu` reads as a violet aurora; `stack` is a subtle ink metallic.
 * Meant to be dropped inside a container that sets its font-size.
 */
export function HeroWordmark() {
  return (
    <span className={styles.mark} aria-label="nustack">
      <span className={styles.nu} aria-hidden>nu</span>
      <span className={styles.stack} aria-hidden>stack</span>
    </span>
  );
}
