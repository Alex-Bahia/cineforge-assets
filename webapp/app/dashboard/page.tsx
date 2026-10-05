"use client"

import { useState } from "react"
import Link from "next/link"

type Tab = "overview" | "channels" | "jobs" | "nichos" | "downloader"

const MOCK_CHANNELS = [
  { id: 1, name: "Finance Dark BR", niche: "Finance", videos: 47, views: "312K", revenue: "R$1.840", status: "active" },
  { id: 2, name: "Tech Insider", niche: "Tech", videos: 23, views: "89K", revenue: "R$620", status: "active" },
  { id: 3, name: "Mundo Kids", niche: "Kids", videos: 61, views: "1.2M", revenue: "R$3.200", status: "active" },
]

const MOCK_JOBS = [
  { id: "job_001", title: "Os Segredos que os Bancos Escondem", status: "completed", duration: "8m32s", channel: "Finance Dark BR", created: "há 2h" },
  { id: "job_002", title: "IA que Substitui Médicos em 2026", status: "running", duration: "–", channel: "Tech Insider", created: "há 15min" },
  { id: "job_003", title: "Criança Descobre Tesouro Perdido", status: "queued", duration: "–", channel: "Mundo Kids", created: "há 3min" },
  { id: "job_004", title: "Como Escape Room Mudou Minha Vida", status: "error", duration: "–", channel: "Finance Dark BR", created: "há 5h" },
]

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-500/15 text-green-400 border-green-500/30",
  completed: "bg-green-500/15 text-green-400 border-green-500/30",
  running: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
  queued: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  error: "bg-red-500/15 text-red-400 border-red-500/30",
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<Tab>("overview")
  const [newJobNiche, setNewJobNiche] = useState("finance_dark")
  const [newJobTopic, setNewJobTopic] = useState("")
  const [launching, setLaunching] = useState(false)

  const handleLaunchJob = async (e: React.FormEvent) => {
    e.preventDefault()
    setLaunching(true)
    setTimeout(() => {
      setLaunching(false)
      alert("Job adicionado à fila! Vídeo gerado em ~15 minutos.")
    }, 1500)
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-60 border-r border-white/5 bg-[#0d0d15] flex flex-col">
        <div className="p-5 border-b border-white/5">
          <Link href="/" className="text-xl font-black">
            <span className="text-violet-500">Cine</span>Forge
          </Link>
          <div className="mt-1 text-xs text-gray-500">Dashboard</div>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {([
            { id: "overview", label: "Visão Geral", icon: "📊" },
            { id: "channels", label: "Canais", icon: "📺" },
            { id: "jobs", label: "Jobs", icon: "🎬" },
            { id: "nichos", label: "Niche Strategist", icon: "🔍" },
            { id: "downloader", label: "Turbo Downloader", icon: "⬇️" },
          ] as { id: Tab; label: string; icon: string }[]).map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                activeTab === item.id
                  ? "bg-violet-600/20 text-violet-400 border border-violet-500/30"
                  : "text-gray-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <span>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>
        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-3 rounded-lg bg-white/5 px-3 py-2.5">
            <div className="h-8 w-8 rounded-full bg-violet-600 flex items-center justify-center text-sm font-bold">
              J
            </div>
            <div>
              <div className="text-sm font-medium">João Silva</div>
              <div className="text-xs text-gray-500">Plano Pro</div>
            </div>
          </div>
          <Link
            href="/login"
            className="mt-2 block w-full rounded-lg px-3 py-2 text-center text-xs text-gray-500 hover:text-white hover:bg-white/5 transition-colors"
          >
            Sair
          </Link>
        </div>
      </div>

      {/* Main content */}
      <div className="ml-60 p-8">
        {/* Overview */}
        {activeTab === "overview" && (
          <div>
            <h1 className="text-2xl font-bold mb-2">Visão Geral</h1>
            <p className="text-gray-400 mb-8">Resumo da sua operação CineForge</p>

            <div className="grid grid-cols-4 gap-4 mb-8">
              {[
                { label: "Vídeos este mês", value: "47", change: "+12 vs mês anterior", icon: "🎬" },
                { label: "Views totais", value: "1.6M", change: "+340K este mês", icon: "👁️" },
                { label: "Receita estimada", value: "R$5.660", change: "+18% vs mês anterior", icon: "💰" },
                { label: "Canais ativos", value: "3", change: "Limite: 3 (Pro)", icon: "📺" },
              ].map((stat) => (
                <div key={stat.label} className="rounded-2xl border border-white/8 bg-white/3 p-5">
                  <div className="text-2xl mb-2">{stat.icon}</div>
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <div className="text-sm text-gray-400 mt-0.5">{stat.label}</div>
                  <div className="text-xs text-green-400 mt-2">{stat.change}</div>
                </div>
              ))}
            </div>

            {/* Quick launch */}
            <div className="rounded-2xl border border-violet-500/30 bg-violet-900/10 p-6 mb-8">
              <h2 className="text-lg font-bold mb-4">⚡ Lançar novo vídeo</h2>
              <form onSubmit={handleLaunchJob} className="flex gap-4">
                <select
                  value={newJobNiche}
                  onChange={(e) => setNewJobNiche(e.target.value)}
                  className="rounded-lg border border-white/10 bg-[#12121a] px-4 py-2.5 text-sm text-white focus:border-violet-500 focus:outline-none"
                >
                  <option value="finance_dark">Finance Dark</option>
                  <option value="tech">Tech & AI</option>
                  <option value="health">Health & Wellness</option>
                  <option value="kids">Kids & Family</option>
                  <option value="education">Education</option>
                </select>
                <input
                  type="text"
                  value={newJobTopic}
                  onChange={(e) => setNewJobTopic(e.target.value)}
                  required
                  placeholder="Tópico do vídeo (ex: Os Segredos que os Bancos Escondem)"
                  className="flex-1 rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:border-violet-500 focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={launching}
                  className="rounded-lg bg-violet-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-violet-500 disabled:opacity-50 transition-colors"
                >
                  {launching ? "Lançando..." : "Lançar"}
                </button>
              </form>
            </div>

            {/* Recent jobs */}
            <div className="rounded-2xl border border-white/8 bg-white/3 overflow-hidden">
              <div className="px-6 py-4 border-b border-white/8 flex items-center justify-between">
                <h2 className="font-bold">Jobs recentes</h2>
                <button onClick={() => setActiveTab("jobs")} className="text-xs text-violet-400 hover:text-violet-300">
                  Ver todos →
                </button>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/5 text-gray-500">
                    <th className="px-6 py-3 text-left font-medium">Título</th>
                    <th className="px-6 py-3 text-left font-medium">Canal</th>
                    <th className="px-6 py-3 text-left font-medium">Status</th>
                    <th className="px-6 py-3 text-left font-medium">Criado</th>
                  </tr>
                </thead>
                <tbody>
                  {MOCK_JOBS.slice(0, 3).map((job) => (
                    <tr key={job.id} className="border-b border-white/5 hover:bg-white/2 transition-colors">
                      <td className="px-6 py-4 text-white">{job.title}</td>
                      <td className="px-6 py-4 text-gray-400">{job.channel}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[job.status]}`}>
                          {job.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-gray-500">{job.created}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Channels */}
        {activeTab === "channels" && (
          <div>
            <div className="flex items-center justify-between mb-8">
              <div>
                <h1 className="text-2xl font-bold mb-1">Canais</h1>
                <p className="text-gray-400">3 de 3 canais ativos (limite do plano Pro)</p>
              </div>
              <button className="rounded-lg border border-violet-500/50 px-4 py-2 text-sm text-violet-400 hover:bg-violet-500/10 transition-colors">
                + Adicionar canal
              </button>
            </div>
            <div className="grid gap-4">
              {MOCK_CHANNELS.map((ch) => (
                <div key={ch.id} className="rounded-2xl border border-white/8 bg-white/3 p-6 flex items-center gap-6">
                  <div className="h-12 w-12 rounded-xl bg-violet-600/20 flex items-center justify-center text-xl font-bold text-violet-400 shrink-0">
                    {ch.name[0]}
                  </div>
                  <div className="flex-1">
                    <div className="font-bold">{ch.name}</div>
                    <div className="text-sm text-gray-400">{ch.niche}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold">{ch.videos}</div>
                    <div className="text-xs text-gray-500">vídeos</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold">{ch.views}</div>
                    <div className="text-xs text-gray-500">views</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold text-green-400">{ch.revenue}</div>
                    <div className="text-xs text-gray-500">receita/mês</div>
                  </div>
                  <span className={`rounded-full border px-3 py-1 text-xs font-medium ${STATUS_COLORS[ch.status]}`}>
                    {ch.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Jobs */}
        {activeTab === "jobs" && (
          <div>
            <h1 className="text-2xl font-bold mb-2">Jobs de produção</h1>
            <p className="text-gray-400 mb-8">Histórico e status de todos os vídeos</p>
            <div className="rounded-2xl border border-white/8 bg-white/3 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/8 text-gray-500">
                    <th className="px-6 py-4 text-left font-medium">ID</th>
                    <th className="px-6 py-4 text-left font-medium">Título</th>
                    <th className="px-6 py-4 text-left font-medium">Canal</th>
                    <th className="px-6 py-4 text-left font-medium">Duração</th>
                    <th className="px-6 py-4 text-left font-medium">Status</th>
                    <th className="px-6 py-4 text-left font-medium">Criado</th>
                  </tr>
                </thead>
                <tbody>
                  {MOCK_JOBS.map((job) => (
                    <tr key={job.id} className="border-b border-white/5 hover:bg-white/2 transition-colors">
                      <td className="px-6 py-4 font-mono text-xs text-gray-500">{job.id}</td>
                      <td className="px-6 py-4 text-white">{job.title}</td>
                      <td className="px-6 py-4 text-gray-400">{job.channel}</td>
                      <td className="px-6 py-4 text-gray-400">{job.duration}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[job.status]}`}>
                          {job.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-gray-500">{job.created}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Niche Strategist */}
        {activeTab === "nichos" && (
          <div>
            <h1 className="text-2xl font-bold mb-2">Niche Strategist</h1>
            <p className="text-gray-400 mb-8">Framework 4 fases para identificar nichos lucrativos</p>
            <div className="grid gap-6 lg:grid-cols-2">
              {[
                {
                  fase: "01", title: "Mapeamento",
                  desc: "Google Trends + autocomplete revela intenções não monetizadas. Volume x CPM x saturação.",
                  status: "Disponível",
                  icon: "🗺️",
                },
                {
                  fase: "02", title: "Validação por Outliers",
                  desc: "Analisa os 10 outliers de performance do nicho. Um vídeo com 10x mais views que a média = oportunidade real.",
                  status: "Disponível",
                  icon: "📈",
                },
                {
                  fase: "03", title: "Produção",
                  desc: "Hook <15s, keyword falada verbalmente, thumbnail A/B, SEO técnico. Guidelines automáticas por nicho.",
                  status: "Disponível",
                  icon: "🎬",
                },
                {
                  fase: "04", title: "Análise CTR × Retenção",
                  desc: "Diagnóstico matricial dos 4 quadrantes. CTR alvo >7%, Retenção alvo >35%. Ações específicas por situação.",
                  status: "Disponível",
                  icon: "📊",
                },
              ].map((item) => (
                <div key={item.fase} className="rounded-2xl border border-white/8 bg-white/3 p-6">
                  <div className="flex items-start gap-4 mb-4">
                    <span className="text-3xl">{item.icon}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs text-violet-400 bg-violet-500/10 rounded-full px-2 py-0.5 font-mono">
                          Fase {item.fase}
                        </span>
                        <span className="text-xs text-green-400">{item.status}</span>
                      </div>
                      <h3 className="font-bold text-lg">{item.title}</h3>
                    </div>
                  </div>
                  <p className="text-sm text-gray-400 leading-relaxed">{item.desc}</p>
                  <button className="mt-4 text-sm text-violet-400 hover:text-violet-300 transition-colors">
                    Executar análise →
                  </button>
                </div>
              ))}
            </div>

            {/* CPM table */}
            <div className="mt-8 rounded-2xl border border-white/8 bg-white/3 overflow-hidden">
              <div className="px-6 py-4 border-b border-white/8">
                <h2 className="font-bold">CPM por nicho (estimativa US market)</h2>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/5 text-gray-500">
                    <th className="px-6 py-3 text-left font-medium">Nicho</th>
                    <th className="px-6 py-3 text-left font-medium">CPM Mín</th>
                    <th className="px-6 py-3 text-left font-medium">CPM Máx</th>
                    <th className="px-6 py-3 text-left font-medium">Saturação</th>
                    <th className="px-6 py-3 text-left font-medium">Score Oportunidade</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { niche: "Finance / Investing", min: "$15", max: "$40", sat: "Alta", score: "8.2/10" },
                    { niche: "Tech & AI", min: "$12", max: "$35", sat: "Média", score: "8.7/10" },
                    { niche: "Health & Wellness", min: "$10", max: "$25", sat: "Média", score: "7.9/10" },
                    { niche: "Education", min: "$8", max: "$20", sat: "Baixa", score: "7.5/10" },
                    { niche: "Kids & Family", min: "$3", max: "$8", sat: "Alta", score: "6.1/10" },
                    { niche: "Investigação / Crime", min: "$10", max: "$28", sat: "Baixa", score: "8.9/10" },
                  ].map((row) => (
                    <tr key={row.niche} className="border-b border-white/5 hover:bg-white/2">
                      <td className="px-6 py-3 font-medium">{row.niche}</td>
                      <td className="px-6 py-3 text-green-400">{row.min}</td>
                      <td className="px-6 py-3 text-green-400 font-bold">{row.max}</td>
                      <td className="px-6 py-3 text-gray-400">{row.sat}</td>
                      <td className="px-6 py-3 font-mono text-violet-400">{row.score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Turbo Downloader */}
        {activeTab === "downloader" && (
          <div>
            <h1 className="text-2xl font-bold mb-2">Turbo Downloader</h1>
            <p className="text-gray-400 mb-8">Capture vídeos virais para modelagem de edição em massa</p>

            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-2xl border border-white/8 bg-white/3 p-6">
                <h2 className="font-bold mb-4">Adicionar fonte de referência</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1.5">URL do canal / perfil</label>
                    <input
                      type="url"
                      placeholder="https://youtube.com/@FinanceExpert ou https://tiktok.com/@creator"
                      className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-violet-500 focus:outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm text-gray-400 mb-1.5">Nicho</label>
                      <select className="w-full rounded-lg border border-white/10 bg-[#12121a] px-3 py-2.5 text-sm text-white focus:border-violet-500 focus:outline-none">
                        <option>Finance Dark</option>
                        <option>Tech & AI</option>
                        <option>Health</option>
                        <option>Kids</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-400 mb-1.5">Views mínimas</label>
                      <select className="w-full rounded-lg border border-white/10 bg-[#12121a] px-3 py-2.5 text-sm text-white focus:border-violet-500 focus:outline-none">
                        <option>500K</option>
                        <option>1M</option>
                        <option>5M</option>
                      </select>
                    </div>
                  </div>
                  <button className="w-full rounded-xl bg-violet-600 py-3 text-sm font-semibold text-white hover:bg-violet-500 transition-colors">
                    Iniciar download →
                  </button>
                </div>
              </div>

              <div className="rounded-2xl border border-white/8 bg-white/3 p-6">
                <h2 className="font-bold mb-4">Edit Models gerados</h2>
                <div className="space-y-3">
                  {[
                    { niche: "Finance Dark", videos: 12, avgScene: "3.2s", scenesPerMin: 18.7, hookDur: "14s" },
                    { niche: "Tech & AI", videos: 8, avgScene: "4.1s", scenesPerMin: 14.6, hookDur: "12s" },
                  ].map((model) => (
                    <div key={model.niche} className="rounded-xl border border-white/8 bg-white/2 p-4">
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-semibold">{model.niche}</span>
                        <span className="text-xs text-gray-500">{model.videos} vídeos analisados</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="rounded-lg bg-white/5 p-2">
                          <div className="text-sm font-bold text-cyan-400">{model.avgScene}</div>
                          <div className="text-xs text-gray-500">cena média</div>
                        </div>
                        <div className="rounded-lg bg-white/5 p-2">
                          <div className="text-sm font-bold text-violet-400">{model.scenesPerMin}</div>
                          <div className="text-xs text-gray-500">cortes/min</div>
                        </div>
                        <div className="rounded-lg bg-white/5 p-2">
                          <div className="text-sm font-bold text-yellow-400">{model.hookDur}</div>
                          <div className="text-xs text-gray-500">hook</div>
                        </div>
                      </div>
                    </div>
                  ))}
                  {MOCK_CHANNELS.length === 0 && (
                    <p className="text-sm text-gray-500 text-center py-4">
                      Nenhum modelo gerado ainda. Adicione uma fonte de referência.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
