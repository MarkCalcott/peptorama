import styles from "./Topbar.module.css";

export default function Topbar() {
  return (
    <div className={styles.toolbar}>
      <img className={styles.logo} src="/logo.svg" alt="Peptorama logo" />
      <h1>Peptorama</h1>
    </div>
  );
}
