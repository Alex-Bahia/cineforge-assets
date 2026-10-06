import styles from "./StatusBar.module.css"

interface Provider {
  name: string
  status: "online" | "offline" | "degraded"
  latency_ms?: number
}

interface Props {
  providers: Provider[]
  online: boolean
}

export default function StatusBar({ providers, online }: Props) {
  const fps = online ? "120" : "—"
  const net = online ? "12.4 TB/S" : "—"

  return (
    <footer className={styles.bar}>
      <span>FPS {fps}</span>
      <span>·</span>
      <span>RES 8K</span>
      <span>·</span>
      <span>NET {net}</span>
      {providers.map((p) => (
        <span key={p.name} className={p.status === "online" ? styles.ok : styles.err}>
          {p.name.toUpperCase()} {p.latency_ms != null ? `${p.latency_ms}ms` : p.status.toUpperCase()}
        </span>
      ))}
    </footer>
  )
}
