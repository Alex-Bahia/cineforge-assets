import { useMemo } from "react"
import { useBackend } from "../useBackend"
import ModuleCard from "../components/ModuleCard"
import StatusBar from "../components/StatusBar"
import Globe from "../components/Globe"
import styles from "./Cockpit.module.css"

interface ModuleDef {
  id: string
  label: string
  icon: string
  endpoint?: string
  getValue?: (b: ReturnType<typeof useBackend>) => string
  getStatus?: (b: ReturnType<typeof useBackend>) => "active" | "idle" | "offline"
}

const MODULES: ModuleDef[] = [
  {
    id: "roteiro",
    label: "ROTEIRO IA",
    icon: "✦",
    getValue: (b) => `${b.queued} em fila`,
    getStatus: (b) => (b.online ? "active" : "offline"),
  },
  {
    id: "trilha",
    label: "TRILHA NEURAL",
    icon: "◈",
    getValue: () => "ElevenLabs",
    getStatus: (b) => (b.online ? "idle" : "offline"),
  },
  {
    id: "legacy",
    label: "LEGACY CLONING",
    icon: "⬡",
    getValue: (b) => `${b.jobs} jobs`,
    getStatus: (b) => (b.jobs > 0 ? "active" : "idle"),
  },
  {
    id: "games",
    label: "GAMES UNIVERSE",
    icon: "◇",
    getValue: () => "Em breve",
    getStatus: () => "idle",
  },
  {
    id: "influencers",
    label: "INFLUENCERS",
    icon: "◉",
    getValue: (b) => `${b.channels} canais`,
    getStatus: (b) => (b.channels > 0 ? "active" : "idle"),
  },
  {
    id: "dna",
    label: "DNA SEQUENCER",
    icon: "⟁",
    getValue: () => "Análise",
    getStatus: (b) => (b.online ? "idle" : "offline"),
  },
  {
    id: "storyboard",
    label: "STORYBOARD",
    icon: "▣",
    getValue: () => "Visual AI",
    getStatus: (b) => (b.online ? "idle" : "offline"),
  },
  {
    id: "dublagem",
    label: "DUBLAGEM AI",
    icon: "◎",
    getValue: () => "ElevenLabs",
    getStatus: (b) => {
      const p = b.providers.find((x) => x.name === "elevenlabs")
      return p?.status === "online" ? "active" : "offline"
    },
  },
  {
    id: "edicao",
    label: "EDIÇÃO TÁTICA",
    icon: "◫",
    getValue: (b) => (b.jobs > 0 ? `${b.jobs} editando` : "Standby"),
    getStatus: (b) => (b.jobs > 0 ? "active" : "idle"),
  },
  {
    id: "color",
    label: "COLOR GRADE",
    icon: "◑",
    getValue: () => "HDR10",
    getStatus: (b) => (b.online ? "idle" : "offline"),
  },
  {
    id: "render",
    label: "RENDER 8K",
    icon: "◈",
    getValue: (b) => {
      const p = b.providers.find((x) => x.name === "render" || x.name === "gpu")
      return p ? `${p.latency_ms ?? "—"}ms` : "—"
    },
    getStatus: (b) => {
      const p = b.providers.find((x) => x.name === "render" || x.name === "gpu")
      return p?.status === "online" ? "active" : b.online ? "idle" : "offline"
    },
  },
  {
    id: "deploy",
    label: "DEPLOY GLOBAL",
    icon: "⬢",
    getValue: (b) => `${b.jobs} publicados`,
    getStatus: (b) => (b.online ? "active" : "offline"),
  },
]

export default function Cockpit() {
  const backend = useBackend(15000)

  const modules = useMemo(
    () =>
      MODULES.map((m) => ({
        ...m,
        value: m.getValue?.(backend) ?? "—",
        status: m.getStatus?.(backend) ?? "idle",
      })),
    [backend]
  )

  return (
    <div className={styles.root}>
      {/* Scanline overlay — pure CSS, zero JS */}
      <div className={styles.scanlines} aria-hidden />

      {/* Header */}
      <header className={styles.header}>
        <span className={styles.logo}>IAI STUDIOS</span>
        <div className={styles.status}>
          <span className={backend.online ? styles.dot_green : styles.dot_red} />
          {backend.online ? "BACKEND ONLINE" : "BACKEND OFFLINE"}
        </div>
        <span className={styles.ts}>
          {backend.lastUpdate > 0
            ? new Date(backend.lastUpdate).toLocaleTimeString("pt-BR")
            : "—"}
        </span>
      </header>

      {/* Main grid */}
      <main className={styles.grid}>
        <section className={styles.modules}>
          {modules.map((m) => (
            <ModuleCard
              key={m.id}
              label={m.label}
              icon={m.icon}
              value={m.value}
              status={m.status}
            />
          ))}
        </section>

        <aside className={styles.side}>
          <Globe online={backend.online} />
          <div className={styles.stats}>
            <Stat label="JOBS" value={String(backend.jobs)} />
            <Stat label="FILA" value={String(backend.queued)} />
            <Stat label="CANAIS" value={String(backend.channels)} />
            <Stat
              label="PROVIDERS"
              value={String(backend.providers.filter((p) => p.status === "online").length)}
            />
          </div>
        </aside>
      </main>

      {/* Footer */}
      <StatusBar providers={backend.providers} online={backend.online} />
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.stat}>
      <span className={styles.stat_label}>{label}</span>
      <span className={styles.stat_value}>{value}</span>
    </div>
  )
}
