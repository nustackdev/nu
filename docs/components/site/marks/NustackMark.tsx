import styles from './NustackMark.module.css';

type Props = {
  className?: string;
  /** Both parts inherit currentColor instead of the branded purple/white split. */
  mono?: boolean;
};

export function NustackMark({ className, mono }: Props) {
  const cls = [styles.mark, mono && styles.mono, className].filter(Boolean).join(' ');
  return (
    <span className={cls}>
      <span className={styles.nu}>nu</span><span className={styles.stack}>stack</span>
    </span>
  );
}
