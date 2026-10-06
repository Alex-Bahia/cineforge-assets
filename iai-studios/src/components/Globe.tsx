import styles from "./Globe.module.css"

interface Props {
  online: boolean
}

export default function Globe({ online }: Props) {
  return (
    <div className={styles.root}>
      <div className={styles.ring1} />
      <div className={styles.ring2} />
      <div className={styles.ring3} />
      <div className={styles.ring4} />
      <div className={`${styles.core} ${online ? styles.core_on : ""}`} />
      <div className={styles.label}>{online ? "CONECTADO" : "OFFLINE"}</div>
    </div>
  )
}
