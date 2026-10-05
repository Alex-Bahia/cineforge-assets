"use client"

import { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import {
  listJobs, createJob, cancelJob, getQueueStats,
  listChannels, getChannelQuota,
  scanOpportunities, startDownloader, listEditModels,
  getNicheOpportunities, auditCtr, getWeeklyReport,
  getProvidersStatus, getHealth,
  type Job, type Channel, type EditModel, type NicheOpportunity, type ProviderStatus,
} from "@/lib/api"

type Tab = "overview" | "channels" | "jobs" | "nichos" | "downloader" | "providers"

const STATUS_COLORS: Record<string, string> = {
  active:    "bg-green-500/15 text-green-400 border-green-500/30",
  done:      "bg-green-500/15 text-green-400 border-green-500/30",
  running:   "bg-cyan-500/15 text-cyan-400 border-cyan-500/30 animate-pulse",
  pending:   "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  retry:     "bg-orange-500/15 text-orange-400 border-orange-500/30",
  failed:    "bg-red-500/15 text-red-400 border-red-500/30",
  error:     "bg-red-500/15 text-red-400 border-red-500/30",
  queued:    "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  available: "bg-green-500/15 text-green-400 border-green-500/30",
}

function fmtTime(ts: number | null) {
  if (!ts) return "–"
  const d = new Date(ts * 1000)
  const diff = Math.floor((Date.now() / 1000) - ts)
  if (diff < 60) return `há ${diff}s`
  if (diff < 3600) return `há ${Math.floor(diff / 60)}min`
  if (diff < 86400) return `há ${Math.floor(diff / 3600)}h`
  return d.toLocaleDateString("pt-BR")
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<Tab>("overview")
  const [backendOk, setBackendOk] = useState<boolean | null>(null)

  // Jobs state
  const [jobs, setJobs] = useState<Job[]>([])
  const [jobsLoading, setJobsLoading] = useState(false)
  const [queueStats, setQueueStats] = useState<Record<string, number>>({})

  // Channels state
  const [channels, setChannels] = useState<Channel[]>([])
  const [channelQuotas, setChannelQuotas] = useState<Record<string, { used_today: number; remaining_today: number; can_upload: boolean; daily_limit: number }>>({})

  // New job form
  const [newJobNiche, setNewJobNiche] = useState("dark")
  const [newJobTopic, setNewJobTopic] = useState("")
  const [launching, setLaunching] = useState(false)
  const [launchMsg, setLaunchMsg] = useState("")

  // Niche state
  const [nicheFilter, setNicheFilter] = useState("finance_dark")
  const [nicheMarket, setNicheMarket] = useState("US")
  const [nicheOpps, setNicheOpps] = useState<NicheOpportunity[]>([])
  const [nicheLoading, setNicheLoading] = useState(false)
  const [weeklyReport, setWeeklyReport] = useState("")
  const [auditForm, setAuditForm] = useState({ ctr: "4.5", retention: "30", niche: "finance_dark" })
  const [auditResult, setAuditResult] = useState<Record<string, unknown> | null>(null)

  // Downloader state
  const [dlUrl, setDlUrl] = useState("")
  const [dlNiche, setDlNiche] = useState("dark")
  const [dlMinViews, setDlMinViews] = useState("500000")
  const [dlLoading, setDlLoading] = useState(false)
  const [dlTaskId, setDlTaskId] = useState("")
  const [dlStatus, setDlStatus] = useState("")
  const [editModels, setEditModels] = useState<EditModel[]>([])

  // Providers state
  const [providers, setProviders] = useState<Record<string, ProviderStatus>>({})
  const [providersLoading, setProvidersLoading] = useState(false)

  // ── Health check ──────────────────────────────────────────────────────────
  useEffect(() => {
    getHealth()
      .then(() => setBackendOk(true))
      .catch(() => setBackendOk(false))
  }, [])

  // ── Auto-refresh jobs ─────────────────────────────────────────────────────
  const loadJobs = useCallback(async () => {
    setJobsLoading(true)
    try {
      const [jobsRes, statsRes] = await Promise.all([listJobs({ limit: 100 }), getQueueStats()])
      setJobs(jobsRes.jobs)
      const s = statsRes as Record<string, unknown>
      setQueueStats({ pending: Number(s.pending ?? 0), running: Number(s.running ?? 0), done: Number(s.done ?? 0), failed: Number(s.failed ?? 0) })
    } catch { /* backend offline */ }
    finally { setJobsLoading(false) }
  }, [])

  useEffect(() => {
    loadJobs()
    const iv = setInterval(loadJobs, 15_000) // refresh a cada 15s
    return () => clearInterval(iv)
  }, [loadJobs])

  // ── Load channels ─────────────────────────────────────────────────────────
  useEffect(() => {
    listChannels().then(r => {
      setChannels(r.channels)
      r.channels.forEach(ch => {
        getChannelQuota(ch.channel_id).then(q => {
          setChannelQuotas(prev => ({ ...prev, [ch.channel_id]: q }))
        }).catch(() => {})
      })
    }).catch(() => {})
  }, [])

  // ── Load edit models ──────────────────────────────────────────────────────
  useEffect(() => {
    listEditModels().then(r => setEditModels(r.models)).catch(() => {})
  }, [])

  // ── Handlers ─────────────────────────────────────────────────────────────
  const handleLaunchJob = async (e: React.FormEvent) => {
    e.preventDefault()
    setLaunching(true)
    setLaunchMsg("")
    try {
      const res = await createJob({ topic: newJobTopic, niche: newJobNiche })
      setLaunchMsg(`✓ Job ${res.job_id} adicionado à fila!`)
      setNewJobTopic("")
      loadJobs()
    } catch (err) {
      setLaunchMsg(`✗ Erro: ${err}`)
    } finally {
      setLaunching(false)
    }
  }

  const handleCancelJob = async (jobId: string) => {
    await cancelJob(jobId).catch(() => {})
    loadJobs()
  }

  const handleScan = async () => {
    setLaunching(true)
    try {
      const res = await scanOpportunities(newJobNiche, 5)
      setLaunchMsg(`✓ ${res.jobs_created} jobs de scan criados para "${newJobNiche}"`)
      loadJobs()
    } catch (err) {
      setLaunchMsg(`✗ Erro: ${err}`)
    } finally {
      setLaunching(false)
    }
  }

  const handleLoadNiche = async () => {
    setNicheLoading(true)
    try {
      const res = await getNicheOpportunities(nicheFilter, nicheMarket)
      setNicheOpps(res.opportunities)
    } catch { setNicheOpps([]) }
    finally { setNicheLoading(false) }
  }

  const handleWeeklyReport = async () => {
    try {
      const res = await getWeeklyReport(nicheFilter, nicheMarket)
      setWeeklyReport(res.report)
    } catch (err) {
      setWeeklyReport(`Erro: ${err}`)
    }
  }

  const handleAudit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const res = await auditCtr({
        ctr_estimate: parseFloat(auditForm.ctr),
        avg_view_duration_pct: parseFloat(auditForm.retention),
        niche: auditForm.niche,
      })
      setAuditResult(res as Record<string, unknown>)
    } catch (err) {
      setAuditResult({ error: String(err) })
    }
  }

  const handleStartDownloader = async (e: React.FormEvent) => {
    e.preventDefault()
    setDlLoading(true)
    setDlStatus("")
    setDlTaskId("")
    try {
      const res = await startDownloader({ url: dlUrl, niche: dlNiche, min_views: parseInt(dlMinViews) })
      setDlTaskId(res.task_id)
      setDlStatus("queued")
      // Poll status
      const poll = setInterval(async () => {
        try {
          const s = await (await fetch(`/api/backend/downloader/status/${res.task_id}`)).json()
          setDlStatus(s.status)
          if (s.status === "done" || s.status === "error") {
            clearInterval(poll)
            listEditModels().then(r => setEditModels(r.models)).catch(() => {})
          }
        } catch { clearInterval(poll) }
      }, 3000)
    } catch (err) {
      setDlStatus(`error: ${err}`)
    } finally {
      setDlLoading(false)
    }
  }

  const handleLoadProviders = async () => {
    setProvidersLoading(true)
    try {
      const res = await getProvidersStatus()
      setProviders(res)
    } catch { setProviders({}) }
    finally { setProvidersLoading(false) }
  }

  useEffect(() => {
    if (activeTab === "providers") handleLoadProviders()
  }, [activeTab]) // eslint-disable-line react-hooks/exhaustive-deps

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-60 border-r border-white/5 bg-[#0d0d15] flex flex-col z-10">
        <div className="p-5 border-b border-white/5">
          <Link href="/" className="text-xl font-black">
            <span className="text-violet-500">Cine</span>Forge
          </Link>
          <div className="mt-1 flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${backendOk === true ? "bg-green-400" : backendOk === false ? "bg-red-400" : "bg-yellow-400"}`} />
            <span className="text-xs text-gray-500">
              {backendOk === true ? "Backend online" : backendOk === false ? "Backend offline" : "Verificando..."}
            </span>
          </div>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {([
            { id: "overview",   label: "Visão Geral",       icon: "📊" },
            { id: "channels",   label: "Canais",             icon: "📺" },
            { id: "jobs",       label: "Jobs",               icon: "🎬" },
            { id: "nichos",     label: "Niche Strategist",   icon: "🔍" },
            { id: "downloader", label: "Turbo Downloader",   icon: "⬇️" },
            { id: "providers",  label: "Providers IA",       icon: "🤖" },
          ] as { id: Tab; label: string; icon: string }[]).map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                activeTab === item.id
                  ? "bg-violet-600/20 text-violet-400 border border-violet-500/30"
                  : "text-gray-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <span>{item.icon}</span>{item.label}
            </button>
          ))}
        </nav>
        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-3 rounded-lg bg-white/5 px-3 py-2.5 mb-2">
            <div className="h-8 w-8 rounded-full bg-violet-600 flex items-center justify-center text-sm font-bold shrink-0">G</div>
            <div className="overflow-hidden">
              <div className="text-sm font-medium truncate">goforitbrasil</div>
              <div className="text-xs text-gray-500">Plano Pro</div>
            </div>
          </div>
          <Link href="/login" className="block w-full rounded-lg px-3 py-2 text-center text-xs text-gray-500 hover:text-white hover:bg-white/5 transition-colors">
            Sair
          </Link>
        </div>
      </div>

      {/* Main */}
      <div className="ml-60 flex-1 p-8 min-h-screen">

        {/* Backend offline banner */}
        {backendOk === false && (
          <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-sm text-red-300">
            <strong>Backend CineForge offline.</strong> Inicie o servidor Python:{" "}
            <code className="font-mono bg-red-900/30 px-2 py-0.5 rounded">python -m src.api.server</code>{" "}
            ou{" "}
            <code className="font-mono bg-red-900/30 px-2 py-0.5 rounded">uvicorn src.api.server:app --port 8765 --reload</code>
          </div>
        )}

        {/* ── OVERVIEW ──────────────────────────────────────────────────── */}
        {activeTab === "overview" && (
          <div>
            <h1 className="text-2xl font-bold mb-2">Visão Geral</h1>
            <p className="text-gray-400 mb-8">Resumo da operação CineForge em tempo real</p>

            <div className="grid grid-cols-4 gap-4 mb-8">
              {[
                { label: "Pendentes",  value: queueStats.pending  ?? "–", icon: "⏳", color: "text-yellow-400" },
                { label: "Rodando",    value: queueStats.running   ?? "–", icon: "⚡", color: "text-cyan-400" },
                { label: "Concluídos", value: queueStats.done      ?? "–", icon: "✅", color: "text-green-400" },
                { label: "Falhas",     value: queueStats.failed    ?? "–", icon: "❌", color: "text-red-400" },
              ].map(s => (
                <div key={s.label} className="rounded-2xl border border-white/8 bg-white/3 p-5">
                  <div className="text-2xl mb-2">{s.icon}</div>
                  <div className={`text-3xl font-black ${s.color}`}>{s.value}</div>
                  <div className="text-sm text-gray-400 mt-0.5">{s.label}</div>
                </div>
              ))}
            </div>

            {/* Quick launch */}
            <div className="rounded-2xl border border-violet-500/30 bg-violet-900/10 p-6 mb-8">
              <h2 className="text-lg font-bold mb-4">⚡ Lançar novo vídeo</h2>
              <form onSubmit={handleLaunchJob} className="flex gap-3 flex-wrap">
                <select
                  value={newJobNiche}
                  onChange={e => setNewJobNiche(e.target.value)}
                  className="rounded-lg border border-white/10 bg-[#12121a] px-4 py-2.5 text-sm text-white focus:border-violet-500 focus:outline-none"
                >
                  {["dark","finance_dark","tech","health","kids","education"].map(n => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
                <input
                  type="text"
                  value={newJobTopic}
                  onChange={e => setNewJobTopic(e.target.value)}
                  placeholder="Tópico (deixe vazio para auto-descoberta)"
                  className="flex-1 min-w-0 rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:border-violet-500 focus:outline-none"
                />
                <button type="submit" disabled={launching || backendOk === false}
                  className="rounded-lg bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-violet-500 disabled:opacity-50 transition-colors">
                  {launching ? "..." : "Lançar"}
                </button>
                <button type="button" onClick={handleScan} disabled={launching || backendOk === false}
                  className="rounded-lg border border-white/10 px-5 py-2.5 text-sm font-semibold text-gray-300 hover:border-violet-500/50 hover:bg-white/5 disabled:opacity-50 transition-colors">
                  🔍 Auto-scan
                </button>
              </form>
              {launchMsg && (
                <div className={`mt-3 text-sm ${launchMsg.startsWith("✓") ? "text-green-400" : "text-red-400"}`}>
                  {launchMsg}
                </div>
              )}
            </div>

            {/* Recent jobs */}
            <div className="rounded-2xl border border-white/8 bg-white/3 overflow-hidden">
              <div className="px-6 py-4 border-b border-white/8 flex items-center justify-between">
                <h2 className="font-bold">Jobs recentes {jobsLoading && <span className="text-xs text-gray-500 ml-2">atualizando...</span>}</h2>
                <button onClick={() => setActiveTab("jobs")} className="text-xs text-violet-400 hover:text-violet-300">Ver todos →</button>
              </div>
              {jobs.length === 0 ? (
                <div className="px-6 py-8 text-center text-sm text-gray-500">
                  {backendOk === false ? "Backend offline — sem dados" : "Nenhum job ainda. Lance o primeiro acima!"}
                </div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/5 text-gray-500 text-left">
                      <th className="px-6 py-3 font-medium">Tópico</th>
                      <th className="px-6 py-3 font-medium">Nicho</th>
                      <th className="px-6 py-3 font-medium">Status</th>
                      <th className="px-6 py-3 font-medium">Criado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobs.slice(0, 5).map(j => (
                      <tr key={j.job_id} className="border-b border-white/5 hover:bg-white/2">
                        <td className="px-6 py-4">{j.topic || <span className="italic text-gray-500">auto</span>}</td>
                        <td className="px-6 py-4 text-gray-400">{j.niche}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[j.status] ?? ""}`}>
                            {j.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-gray-500">{fmtTime(j.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* ── CHANNELS ──────────────────────────────────────────────────── */}
        {activeTab === "channels" && (
          <div>
            <h1 className="text-2xl font-bold mb-2">Canais YouTube</h1>
            <p className="text-gray-400 mb-8">Canais configurados e cota de upload diária</p>

            {channels.length === 0 ? (
              <div className="rounded-2xl border border-white/8 bg-white/3 p-10 text-center">
                <div className="text-4xl mb-3">📺</div>
                <h3 className="font-bold mb-2">Nenhum canal configurado</h3>
                <p className="text-sm text-gray-400 mb-4">
                  Configure um canal via variáveis de ambiente ou arquivo <code className="font-mono bg-white/5 px-1 rounded">config/youtube_CHANNEL_ID.json</code>
                </p>
                <div className="rounded-xl bg-white/5 p-4 text-left text-xs font-mono text-gray-300 max-w-md mx-auto">
                  <div className="text-gray-500 mb-1"># .env</div>
                  <div>YOUTUBE_CHANNEL_ID=UC...</div>
                  <div>YOUTUBE_CLIENT_ID=...</div>
                  <div>YOUTUBE_CLIENT_SECRET=...</div>
                  <div>YOUTUBE_REFRESH_TOKEN=...</div>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {channels.map(ch => {
                  const q = channelQuotas[ch.channel_id]
                  const pct = q ? Math.round((q.used_today / 10_000) * 100) : 0
                  return (
                    <div key={ch.channel_id} className="rounded-2xl border border-white/8 bg-white/3 p-6">
                      <div className="flex items-center gap-4 mb-4">
                        <div className="h-12 w-12 rounded-xl bg-violet-600/20 flex items-center justify-center text-xl font-bold text-violet-400">
                          {ch.channel_id.slice(2, 4).toUpperCase()}
                        </div>
                        <div>
                          <div className="font-bold font-mono text-sm">{ch.channel_id}</div>
                          <div className="text-xs text-gray-500">fonte: {ch.source}</div>
                        </div>
                        {q && (
                          <span className={`ml-auto rounded-full border px-3 py-1 text-xs font-medium ${q.can_upload ? STATUS_COLORS.active : STATUS_COLORS.failed}`}>
                            {q.can_upload ? "Pode fazer upload" : "Cota esgotada"}
                          </span>
                        )}
                      </div>
                      {q && (
                        <>
                          <div className="flex justify-between text-xs text-gray-400 mb-1">
                            <span>Cota usada hoje</span>
                            <span>{q.used_today.toLocaleString()} / 10.000 unidades ({pct}%)</span>
                          </div>
                          <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                            <div className={`h-full rounded-full transition-all ${pct > 80 ? "bg-red-500" : pct > 50 ? "bg-yellow-500" : "bg-green-500"}`}
                              style={{ width: `${pct}%` }} />
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {Math.floor(q.remaining_today / 100)} uploads restantes hoje
                          </div>
                        </>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* ── JOBS ──────────────────────────────────────────────────────── */}
        {activeTab === "jobs" && (
          <div>
            <div className="flex items-center justify-between mb-8">
              <div>
                <h1 className="text-2xl font-bold mb-1">Jobs de produção</h1>
                <p className="text-gray-400">{jobs.length} jobs no total</p>
              </div>
              <button onClick={loadJobs} className="rounded-lg border border-white/10 px-4 py-2 text-sm text-gray-300 hover:border-violet-500/50 hover:bg-white/5 transition-colors">
                ↻ Atualizar
              </button>
            </div>

            {jobs.length === 0 ? (
              <div className="rounded-2xl border border-white/8 bg-white/3 p-12 text-center text-gray-500">
                {backendOk === false ? "Backend offline" : "Nenhum job. Crie o primeiro na aba Visão Geral."}
              </div>
            ) : (
              <div className="rounded-2xl border border-white/8 bg-white/3 overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/8 text-gray-500 text-left">
                      <th className="px-5 py-4 font-medium">ID</th>
                      <th className="px-5 py-4 font-medium">Tópico</th>
                      <th className="px-5 py-4 font-medium">Nicho</th>
                      <th className="px-5 py-4 font-medium">Status</th>
                      <th className="px-5 py-4 font-medium">Criado</th>
                      <th className="px-5 py-4 font-medium">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobs.map(j => (
                      <tr key={j.job_id} className="border-b border-white/5 hover:bg-white/2">
                        <td className="px-5 py-3 font-mono text-xs text-gray-500">{j.job_id}</td>
                        <td className="px-5 py-3">{j.topic || <span className="italic text-gray-500">auto</span>}</td>
                        <td className="px-5 py-3 text-gray-400">{j.niche}</td>
                        <td className="px-5 py-3">
                          <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[j.status] ?? ""}`}>
                            {j.status}
                          </span>
                          {j.error && <div className="text-xs text-red-400 mt-1 max-w-xs truncate">{j.error}</div>}
                        </td>
                        <td className="px-5 py-3 text-gray-500">{fmtTime(j.created_at)}</td>
                        <td className="px-5 py-3">
                          {(j.status === "pending" || j.status === "retry") && (
                            <button onClick={() => handleCancelJob(j.job_id)}
                              className="text-xs text-red-400 hover:text-red-300 transition-colors">
                              Cancelar
                            </button>
                          )}
                          {j.output_path && (
                            <span className="text-xs text-green-400 font-mono">{j.output_path}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ── NICHE STRATEGIST ──────────────────────────────────────────── */}
        {activeTab === "nichos" && (
          <div>
            <h1 className="text-2xl font-bold mb-2">Niche Strategist</h1>
            <p className="text-gray-400 mb-6">Framework 4 fases com dados reais</p>

            {/* Filters */}
            <div className="flex gap-3 mb-6 flex-wrap">
              <select value={nicheFilter} onChange={e => setNicheFilter(e.target.value)}
                className="rounded-lg border border-white/10 bg-[#12121a] px-4 py-2.5 text-sm text-white focus:border-violet-500 focus:outline-none">
                {["finance_dark","tech","health","kids","education","dark"].map(n => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
              <select value={nicheMarket} onChange={e => setNicheMarket(e.target.value)}
                className="rounded-lg border border-white/10 bg-[#12121a] px-4 py-2.5 text-sm text-white focus:border-violet-500 focus:outline-none">
                {["US","UK","DE","BR","CA","AU"].map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
              <button onClick={handleLoadNiche} disabled={nicheLoading || backendOk === false}
                className="rounded-lg bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-violet-500 disabled:opacity-50 transition-colors">
                {nicheLoading ? "Buscando..." : "Buscar oportunidades"}
              </button>
              <button onClick={handleWeeklyReport} disabled={backendOk === false}
                className="rounded-lg border border-white/10 px-5 py-2.5 text-sm text-gray-300 hover:border-violet-500/50 hover:bg-white/5 disabled:opacity-50 transition-colors">
                📋 Relatório semanal
              </button>
            </div>

            {/* Opportunities table */}
            {nicheOpps.length > 0 && (
              <div className="rounded-2xl border border-white/8 bg-white/3 overflow-hidden mb-6">
                <div className="px-6 py-4 border-b border-white/8 font-bold">
                  Oportunidades — {nicheFilter} / {nicheMarket}
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/5 text-gray-500 text-left">
                      <th className="px-6 py-3 font-medium">Keyword</th>
                      <th className="px-6 py-3 font-medium">Score</th>
                      <th className="px-6 py-3 font-medium">CPM estimado</th>
                      <th className="px-6 py-3 font-medium">Volume</th>
                    </tr>
                  </thead>
                  <tbody>
                    {nicheOpps.map(o => (
                      <tr key={o.keyword} className="border-b border-white/5 hover:bg-white/2">
                        <td className="px-6 py-3 font-medium">{o.keyword}</td>
                        <td className="px-6 py-3 font-mono text-violet-400">{o.opportunity_score.toFixed(1)}</td>
                        <td className="px-6 py-3 text-green-400">${o.cpm_estimate.toFixed(0)}</td>
                        <td className="px-6 py-3 text-gray-400">{(o.scores.search_volume * 100).toFixed(0)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* CTR Audit */}
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-2xl border border-white/8 bg-white/3 p-6">
                <h2 className="font-bold mb-4">📊 Diagnóstico CTR × Retenção</h2>
                <form onSubmit={handleAudit} className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">CTR atual (%)</label>
                      <input type="number" step="0.1" value={auditForm.ctr}
                        onChange={e => setAuditForm(f => ({ ...f, ctr: e.target.value }))}
                        className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:border-violet-500 focus:outline-none" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Retenção média (%)</label>
                      <input type="number" step="0.1" value={auditForm.retention}
                        onChange={e => setAuditForm(f => ({ ...f, retention: e.target.value }))}
                        className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:border-violet-500 focus:outline-none" />
                    </div>
                  </div>
                  <select value={auditForm.niche} onChange={e => setAuditForm(f => ({ ...f, niche: e.target.value }))}
                    className="w-full rounded-lg border border-white/10 bg-[#12121a] px-3 py-2 text-sm text-white focus:border-violet-500 focus:outline-none">
                    {["finance_dark","tech","health","kids","education","dark"].map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                  <button type="submit" disabled={backendOk === false}
                    className="w-full rounded-xl bg-violet-600 py-2.5 text-sm font-semibold text-white hover:bg-violet-500 disabled:opacity-50 transition-colors">
                    Diagnosticar
                  </button>
                </form>
                {auditResult && (
                  <div className="mt-4 rounded-xl bg-white/5 p-4 text-sm">
                    {(auditResult.error as string) ? (
                      <div className="text-red-400">{auditResult.error as string}</div>
                    ) : (
                      <>
                        {auditResult.quadrant && (
                          <div className="font-bold mb-2 text-violet-400">{auditResult.quadrant as string}</div>
                        )}
                        <ul className="space-y-1">
                          {((auditResult.priority_actions ?? auditResult.recommendations) as string[] ?? []).map((a, i) => (
                            <li key={i} className="text-gray-300 flex gap-2">
                              <span className="text-violet-400 shrink-0">→</span>{a}
                            </li>
                          ))}
                        </ul>
                      </>
                    )}
                  </div>
                )}
              </div>

              {/* Weekly report */}
              {weeklyReport && (
                <div className="rounded-2xl border border-white/8 bg-white/3 p-6 overflow-auto">
                  <h2 className="font-bold mb-3">📋 Relatório semanal</h2>
                  <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono">{weeklyReport}</pre>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── TURBO DOWNLOADER ──────────────────────────────────────────── */}
        {activeTab === "downloader" && (
          <div>
            <h1 className="text-2xl font-bold mb-2">Turbo Downloader</h1>
            <p className="text-gray-400 mb-8">Capture vídeos virais para modelagem de edição em massa</p>
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-2xl border border-white/8 bg-white/3 p-6">
                <h2 className="font-bold mb-4">Adicionar fonte de referência</h2>
                <form onSubmit={handleStartDownloader} className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1.5">URL do canal / perfil</label>
                    <input type="url" value={dlUrl} onChange={e => setDlUrl(e.target.value)} required
                      placeholder="https://youtube.com/@FinanceExpert"
                      className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-violet-500 focus:outline-none" />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm text-gray-400 mb-1.5">Nicho</label>
                      <select value={dlNiche} onChange={e => setDlNiche(e.target.value)}
                        className="w-full rounded-lg border border-white/10 bg-[#12121a] px-3 py-2.5 text-sm text-white focus:border-violet-500 focus:outline-none">
                        {["dark","finance_dark","tech","health","kids","education"].map(n => <option key={n} value={n}>{n}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-400 mb-1.5">Views mínimas</label>
                      <select value={dlMinViews} onChange={e => setDlMinViews(e.target.value)}
                        className="w-full rounded-lg border border-white/10 bg-[#12121a] px-3 py-2.5 text-sm text-white focus:border-violet-500 focus:outline-none">
                        <option value="500000">500K</option>
                        <option value="1000000">1M</option>
                        <option value="5000000">5M</option>
                      </select>
                    </div>
                  </div>
                  <button type="submit" disabled={dlLoading || backendOk === false}
                    className="w-full rounded-xl bg-violet-600 py-3 text-sm font-semibold text-white hover:bg-violet-500 disabled:opacity-50 transition-colors">
                    {dlLoading ? "Iniciando..." : "Iniciar download →"}
                  </button>
                  {dlTaskId && (
                    <div className="flex items-center gap-3 rounded-xl bg-white/5 p-3 text-sm">
                      <span className={`h-2 w-2 rounded-full shrink-0 ${dlStatus === "done" ? "bg-green-400" : dlStatus === "error" || dlStatus.startsWith("error") ? "bg-red-400" : "bg-yellow-400 animate-pulse"}`} />
                      <span className="text-gray-300">Task <code className="font-mono">{dlTaskId}</code>: <strong>{dlStatus}</strong></span>
                    </div>
                  )}
                </form>
              </div>

              <div className="rounded-2xl border border-white/8 bg-white/3 p-6">
                <h2 className="font-bold mb-4">Edit Models gerados</h2>
                {editModels.length === 0 ? (
                  <p className="text-sm text-gray-500 py-4 text-center">Nenhum modelo gerado ainda.</p>
                ) : (
                  <div className="space-y-3">
                    {editModels.map(m => (
                      <div key={m.niche} className="rounded-xl border border-white/8 bg-white/2 p-4">
                        <div className="flex items-center justify-between mb-3">
                          <span className="font-semibold">{m.niche}</span>
                          <span className="text-xs text-gray-500">{m.source_videos} vídeos analisados</span>
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-center">
                          <div className="rounded-lg bg-white/5 p-2">
                            <div className="text-sm font-bold text-cyan-400">{m.avg_scene_duration_sec?.toFixed(1)}s</div>
                            <div className="text-xs text-gray-500">cena média</div>
                          </div>
                          <div className="rounded-lg bg-white/5 p-2">
                            <div className="text-sm font-bold text-violet-400">{m.scenes_per_minute?.toFixed(1)}</div>
                            <div className="text-xs text-gray-500">cortes/min</div>
                          </div>
                          <div className="rounded-lg bg-white/5 p-2">
                            <div className="text-sm font-bold text-yellow-400">{m.hook_duration_sec?.toFixed(0)}s</div>
                            <div className="text-xs text-gray-500">hook</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── PROVIDERS ─────────────────────────────────────────────────── */}
        {activeTab === "providers" && (
          <div>
            <div className="flex items-center justify-between mb-8">
              <div>
                <h1 className="text-2xl font-bold mb-1">Providers de IA</h1>
                <p className="text-gray-400">Status de cada provider configurado</p>
              </div>
              <button onClick={handleLoadProviders} disabled={providersLoading}
                className="rounded-lg border border-white/10 px-4 py-2 text-sm text-gray-300 hover:border-violet-500/50 hover:bg-white/5 transition-colors">
                {providersLoading ? "..." : "↻ Verificar"}
              </button>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { key: "fal_ai",      label: "fal.ai",       icon: "⚡", desc: "LTX Fast $0,04/s · Wan 2.1 · Kling" },
                { key: "veo3",        label: "Veo 3",         icon: "🎬", desc: "Google DeepMind · $0,15/s · 1080p" },
                { key: "kling",       label: "Kling Pro",     icon: "🎥", desc: "Kuaishou · $0,084/s · motion control" },
                { key: "elevenlabs",  label: "ElevenLabs",    icon: "🎙️", desc: "TTS multi-idioma · clonagem de voz" },
              ].map(p => {
                const s = providers[p.key]
                const available = s?.available
                return (
                  <div key={p.key} className={`rounded-2xl border p-6 transition-colors ${available === true ? "border-green-500/30 bg-green-900/10" : available === false ? "border-red-500/20 bg-red-900/5" : "border-white/8 bg-white/3"}`}>
                    <div className="text-3xl mb-3">{p.icon}</div>
                    <div className="font-bold mb-1">{p.label}</div>
                    <div className="text-xs text-gray-400 mb-3">{p.desc}</div>
                    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${available === true ? STATUS_COLORS.available : available === false ? STATUS_COLORS.failed : "bg-gray-500/15 text-gray-400 border-gray-500/30"}`}>
                      {available === true ? "Disponível" : available === false ? "Indisponível" : "Não verificado"}
                    </span>
                    {s?.models && (
                      <div className="mt-2 text-xs text-gray-500">{s.models.slice(0, 3).join(", ")}</div>
                    )}
                    {s?.error && (
                      <div className="mt-2 text-xs text-red-400 truncate">{s.error}</div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
