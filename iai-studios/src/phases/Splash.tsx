import styles from "./Splash.module.css"

export default function Splash() {
  return (
    <div className={styles.root}>
      <div className={styles.ring1} />
      <div className={styles.ring2} />
      <div className={styles.ring3} />
      <div className={styles.center}>
        <div className={styles.logo}>IAI</div>
        <div className={styles.sub}>INICIALIZAR INTERFACE</div>
        <div className={styles.bar}>
          <div className={styles.fill} />
        </div>
      </div>
    </div>
  )
}
