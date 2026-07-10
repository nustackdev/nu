import styles from './NustackMark.module.css';

type Props = {
  className?: string;
};

export function NustackMark({ className }: Props) {
  return (
    <span className={`${styles.mark}${className ? ` ${className}` : ''}`}>
      <span className={styles.nu}>nu</span><span className={styles.stack}>stack</span>
    </span>
  );
}
