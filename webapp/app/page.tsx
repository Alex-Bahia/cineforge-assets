"use client"

import Link from "next/link"
import { useState } from "react"

const PLANS = [
  {
    id: "starter",
    name: "Starter",
    price: 97,
    period: "mês",
    description: "Para criadores iniciando com automação",
    features: [
      "1 canal YouTube",
      "30 vídeos/mês",
      "Nichos padrão (Finance, Tech, Health)",
      "Upload automático",
      "Relatório semanal",
    ],
    highlight: false,
    cta: "Começar agora",
  },
  {
    id: "pro",
    name: "Pro",
    price: 197,
    period: "mês",
    description: "Para criadores sérios escalando receita",
    features: [
      "3 canais YouTube",
      "100 vídeos/mês",
      "Todos os nichos (+ Kids, Dark, Investigação)",
      "Turbo Downloader de referências virais",
      "Edit Modeler por nicho",
      "Análise CTR × Retenção",
      "Suporte prioritário",
    ],
    highlight: true,
    cta: "Escolher Pro",
  },
  {
    id: "agency",
    name: "Agency",
    price: 497,
    period: "mês",
    description: "Para agências gerenciando múltiplos clientes",
    features: [
      "Canais ilimitados",
      "Vídeos ilimitados",
      "API pública CineForge",
      "White-label dashboard",
      "Niche Strategist avançado",
      "Suporte dedicado via WhatsApp",
      "Onboarding 1:1",
    ],
    highlight: false,
    cta: "Falar com vendas",
  },
]

const STATS = [
  { label: "Vídeos gerados", value: "12.847", icon: "🎬" },
  { label: "Canais ativos", value: "234", icon: "📺" },
  { label: "CPM médio alcançado", value: "$18,40", icon: "💰" },
  { label: "Horas economizadas", value: "48.000h", icon: "⏱️" },
]

const NICHOS = [
  { name: "Finance Dark", cpm: "$15-40", cor: "bg-yellow-500/10 border-yellow-500/30 text-yellow-400" },
  { name: "Tech & AI", cpm: "$12-35", cor: "bg-cyan-500/10 border-cyan-500/30 text-cyan-400" },
  { name: "Health & Wellness", cpm: "$10-25", cor: "bg-green-500/10 border-green-500/30 text-green-400" },
  { name: "Education", cpm: "$8-20", cor: "bg-blue-500/10 border-blue-500/30 text-blue-400" },
  { name: "Kids & Family", cpm: "$3-8", cor: "bg-pink-500/10 border-pink-500/30 text-pink-400" },
  { name: "Investigação", cpm: "$10-28", cor: "bg-purple-500/10 border-purple-500/30 text-purple-400" },
]

export default function LandingPage() {
  const [billingAnnual, setBillingAnnual] = useState(false)

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/5 bg-[#0a0a0f]/80 backdrop-blur-xl">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-2xl font-black tracking-tight">
                <span className="text-violet-500">Cine</span>Forge
              </span>
              <span className="rounded-full bg-violet-500/20 px-2 py-0.5 text-xs text-violet-400">Beta</span>
            </div>
            <div className="hidden items-center gap-8 md:flex">
              <a href="#como-funciona" className="text-sm text-gray-400 hover:text-white transition-colors">Como funciona</a>
              <a href="#nichos" className="text-sm text-gray-400 hover:text-white transition-colors">Nichos</a>
              <a href="#precos" className="text-sm text-gray-400 hover:text-white transition-colors">Preços</a>
            </div>
            <div className="flex items-center gap-3">
              <Link href="/login" className="text-sm text-gray-400 hover:text-white transition-colors">
                Entrar
              </Link>
              <Link
                href="/signup"
                className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 transition-colors"
              >
                Começar grátis
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden px-4 pt-24 pb-20 sm:px-6 lg:px-8">
        <div className="absolute inset-0 bg-gradient-to-br from-violet-900/20 via-transparent to-cyan-900/10" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-96 w-96 rounded-full bg-violet-600/5 blur-3xl" />
        <div className="relative mx-auto max-w-4xl text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-4 py-2 text-sm text-violet-300">
            <span className="h-2 w-2 rounded-full bg-violet-400 animate-pulse" />
            Novo: Suporte a fal.ai + 600 modelos de vídeo
          </div>
          <h1 className="mb-6 text-5xl font-black leading-tight tracking-tight sm:text-7xl">
            Fabrique{" "}
            <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
              canais virais
            </span>{" "}
            no YouTube com IA
          </h1>
          <p className="mx-auto mb-10 max-w-2xl text-lg text-gray-400 leading-relaxed">
            CineForge gera, edita e publica vídeos automaticamente em nichos de alto CPM.
            Narrativa em 2ª pessoa, padrões de edição extraídos de vídeos virais, upload diário sem intervenção humana.
          </p>
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/signup"
              className="rounded-xl bg-violet-600 px-8 py-4 text-base font-semibold text-white hover:bg-violet-500 transition-all hover:scale-105 shadow-lg shadow-violet-900/50"
            >
              Começar grátis por 7 dias →
            </Link>
            <a
              href="#como-funciona"
              className="rounded-xl border border-white/10 px-8 py-4 text-base font-semibold text-gray-300 hover:border-white/20 hover:text-white transition-colors"
            >
              Ver como funciona
            </a>
          </div>
          <p className="mt-4 text-sm text-gray-500">Sem cartão de crédito • Cancele quando quiser</p>
        </div>
      </section>

      {/* Stats */}
      <section className="border-y border-white/5 bg-white/2 px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl">
          <div className="grid grid-cols-2 gap-8 lg:grid-cols-4">
            {STATS.map((s) => (
              <div key={s.label} className="text-center">
                <div className="text-4xl mb-2">{s.icon}</div>
                <div className="text-3xl font-black text-white">{s.value}</div>
                <div className="text-sm text-gray-500 mt-1">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Como funciona */}
      <section id="como-funciona" className="px-4 py-24 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-black mb-4">Como o CineForge funciona</h2>
            <p className="text-gray-400 max-w-xl mx-auto">
              Pipeline completo do nicho ao upload — você só colhe os resultados.
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[
              {
                step: "01",
                title: "Pesquisa de Nicho",
                desc: "Niche Strategist analisa CPM, volume de busca e saturação. Você recebe oportunidades ranqueadas com projeção de receita mensal.",
                icon: "🔍",
              },
              {
                step: "02",
                title: "Captura de Referências",
                desc: "Turbo Downloader coleta os vídeos mais virais do nicho. EditModeler extrai padrões: ritmo de corte, duração de cenas, estrutura de hook.",
                icon: "⬇️",
              },
              {
                step: "03",
                title: "Geração de Script",
                desc: "Motor de Narrativa cria roteiros em 2ª pessoa do singular — perspectiva imersiva que aumenta retenção e passa nos filtros anti-AI do YouTube.",
                icon: "✍️",
              },
              {
                step: "04",
                title: "Produção Visual",
                desc: "VideoRouter seleciona automaticamente o modelo mais custo-eficiente (fal.ai LTX $0,04/s → Kling Pro → Veo3) para cada cena.",
                icon: "🎥",
              },
              {
                step: "05",
                title: "Edição Automatizada",
                desc: "Cortes nos ritmos extraídos das referências virais. Mesmo padrão de edição que funcionou para vídeos com milhões de views.",
                icon: "✂️",
              },
              {
                step: "06",
                title: "Upload & Otimização SEO",
                desc: "Upload automático com título/thumbnail/tags otimizados. Agendamento estratégico baseado nos horários de pico do seu nicho.",
                icon: "🚀",
              },
            ].map((item) => (
              <div
                key={item.step}
                className="rounded-2xl border border-white/8 bg-white/3 p-6 hover:border-violet-500/30 transition-colors"
              >
                <div className="mb-4 flex items-center gap-3">
                  <span className="text-3xl">{item.icon}</span>
                  <span className="text-xs font-mono text-violet-400 bg-violet-500/10 rounded-full px-2 py-1">
                    Passo {item.step}
                  </span>
                </div>
                <h3 className="text-lg font-bold mb-2">{item.title}</h3>
                <p className="text-sm text-gray-400 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Nichos */}
      <section id="nichos" className="px-4 py-24 sm:px-6 lg:px-8 bg-white/2">
        <div className="mx-auto max-w-5xl">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-black mb-4">Nichos de alto CPM suportados</h2>
            <p className="text-gray-400 max-w-xl mx-auto">
              Cada nicho tem templates de narrativa, paleta visual e diretrizes de SEO específicos.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {NICHOS.map((n) => (
              <div
                key={n.name}
                className={`rounded-2xl border px-6 py-5 flex items-center justify-between ${n.cor}`}
              >
                <span className="font-semibold">{n.name}</span>
                <div className="text-right">
                  <div className="text-xs opacity-70">CPM</div>
                  <div className="font-mono font-bold">{n.cpm}</div>
                </div>
              </div>
            ))}
          </div>
          <p className="text-center text-sm text-gray-500 mt-6">
            * CPM estimado para audiência US. Multiplicador geográfico automático por mercado.
          </p>
        </div>
      </section>

      {/* Preços */}
      <section id="precos" className="px-4 py-24 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-8">
            <h2 className="text-4xl font-black mb-4">Planos e preços</h2>
            <p className="text-gray-400 mb-6">Comece grátis por 7 dias. Sem cartão de crédito.</p>
            <div className="inline-flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-1">
              <button
                onClick={() => setBillingAnnual(false)}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                  !billingAnnual ? "bg-violet-600 text-white shadow" : "text-gray-400 hover:text-white"
                }`}
              >
                Mensal
              </button>
              <button
                onClick={() => setBillingAnnual(true)}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                  billingAnnual ? "bg-violet-600 text-white shadow" : "text-gray-400 hover:text-white"
                }`}
              >
                Anual <span className="ml-1 text-xs text-green-400">-20%</span>
              </button>
            </div>
          </div>
          <div className="grid gap-6 lg:grid-cols-3">
            {PLANS.map((plan) => (
              <div
                key={plan.id}
                className={`relative rounded-2xl p-8 transition-all ${
                  plan.highlight
                    ? "border-2 border-violet-500 bg-violet-900/20 shadow-xl shadow-violet-900/30"
                    : "border border-white/10 bg-white/3 hover:border-white/20"
                }`}
              >
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="rounded-full bg-violet-500 px-3 py-1 text-xs font-bold text-white">
                      MAIS POPULAR
                    </span>
                  </div>
                )}
                <div className="mb-6">
                  <h3 className="text-xl font-bold mb-1">{plan.name}</h3>
                  <p className="text-sm text-gray-400">{plan.description}</p>
                </div>
                <div className="mb-6">
                  <span className="text-4xl font-black">
                    R${billingAnnual ? Math.floor(plan.price * 0.8) : plan.price}
                  </span>
                  <span className="text-gray-400">/{plan.period}</span>
                  {billingAnnual && (
                    <div className="text-xs text-green-400 mt-1">
                      Economize R${Math.floor(plan.price * 0.2 * 12)}/ano
                    </div>
                  )}
                </div>
                <ul className="mb-8 space-y-3">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm">
                      <span className="text-violet-400 mt-0.5 shrink-0">✓</span>
                      <span className="text-gray-300">{f}</span>
                    </li>
                  ))}
                </ul>
                <Link
                  href={plan.id === "agency" ? "/contato" : `/signup?plan=${plan.id}`}
                  className={`block w-full rounded-xl py-3 text-center text-sm font-semibold transition-all ${
                    plan.highlight
                      ? "bg-violet-600 text-white hover:bg-violet-500 hover:scale-105"
                      : "border border-white/10 text-white hover:border-violet-500/50 hover:bg-white/5"
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Final */}
      <section className="px-4 py-24 sm:px-6 lg:px-8 bg-gradient-to-br from-violet-900/30 via-transparent to-cyan-900/10">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-4xl font-black mb-4">
            Pronto para automatizar seu próximo canal?
          </h2>
          <p className="text-gray-400 mb-8 text-lg">
            Junte-se a 234 criadores que já estão usando o CineForge para escalar sua receita no YouTube.
          </p>
          <Link
            href="/signup"
            className="inline-block rounded-xl bg-violet-600 px-10 py-4 text-base font-semibold text-white hover:bg-violet-500 transition-all hover:scale-105 shadow-lg shadow-violet-900/50"
          >
            Começar grátis por 7 dias →
          </Link>
          <p className="mt-4 text-sm text-gray-500">Sem cartão de crédito • Setup em 5 minutos</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl flex flex-col items-center gap-6 text-center sm:flex-row sm:justify-between sm:text-left">
          <div>
            <span className="text-lg font-black">
              <span className="text-violet-500">Cine</span>Forge
            </span>
            <p className="text-xs text-gray-500 mt-1">© 2026 CineForge. Todos os direitos reservados.</p>
          </div>
          <div className="flex gap-6 text-sm text-gray-500">
            <Link href="/termos" className="hover:text-white transition-colors">Termos</Link>
            <Link href="/privacidade" className="hover:text-white transition-colors">Privacidade</Link>
            <Link href="/contato" className="hover:text-white transition-colors">Contato</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
