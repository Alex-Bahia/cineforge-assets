import styles from "./ModuleCard.module.css"

interface Props {
  label: string
  icon: string
  value: string
  status: "active" | "idle" | "offline"
}

const STATUS_CLASS = {
  active: styles.active,
  idle: styles.idle,
  offline: styles.offline,
} as const

export default function ModuleCard({ label, icon, value, status }: Props) {
  return (
    <div className={`${styles.card} ${STATUS_CLASS[status]}`}>
      <div className={styles.corner_tl} />
      <div className={styles.corner_br} />
      <div className={styles.icon}>{icon}</div>
      <div className={styles.label}>{label}</div>
      <div className={styles.value}>{value}</div>
      <div className={styles.badge}>{status.toUpperCase()}</div>
    </div>
  )
}
