import { useState, useEffect } from 'react'
import { useAuth } from './AuthContext'

const VPS_HOST = 'http://167.234.255.202:8765'

const PLAN_LABELS: Record<string, { label: string; price: string; features: string[] }> = {
  free: {
    label: 'Free',
    price: 'R$ 0',
    features: ['3 vídeos/mês', 'Sem imagens IA', 'YouTube apenas'],
  },
  creator: {
    label: 'Creator',
    price: 'R$ 49/mês',
    features: ['30 vídeos/mês', 'Imagens IA incluídas', 'YouTube + Instagram + TikTok'],
  },
  pro: {
    label: 'Pro',
    price: 'R$ 147/mês',
    features: ['150 vídeos/mês', 'Imagens IA + Clone de voz', '5 plataformas + Google Drive'],
  },
  studio: {
    label: 'Studio',
    price: 'R$ 397/mês',
    features: ['Vídeos ilimitados', 'Tudo incluso', 'Todas as plataformas'],
  },
}

type Screen = 'login' | 'register' | 'plans'

interface AuthScreenProps {
  onSuccess?: () => void
}

export default function AuthScreen({ onSuccess }: AuthScreenProps) {
  const { login, register, user } = useAuth()
  const [screen, setScreen] = useState<Screen>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [selectedPlan, setSelectedPlan] = useState('free')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [serverOk, setServerOk] = useState<boolean | null>(null)

  useEffect(() => {
    fetch(`${VPS_HOST}/health`)
      .then(r => r.ok ? setServerOk(true) : setServerOk(false))
      .catch(() => setServerOk(false))
  }, [])

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      onSuccess?.()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(name, email, password, selectedPlan)
      onSuccess?.()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const inputCls = `
    w-full bg-black/40 border border-[#1a3a5c] rounded px-3 py-2 text-sm text-[#c0d8f0]
    focus:outline-none focus:border-[#50a0ff] placeholder:text-[#304060]
  `

  const btnCls = `
    w-full py-2 rounded text-sm font-bold tracking-wider transition-all
    bg-[#50a0ff] hover:bg-[#70b8ff] text-black disabled:opacity-40
  `

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50"
         style={{ background: 'rgba(5,8,20,0.97)', backdropFilter: 'blur(6px)' }}>

      {/* Server status */}
      <div className="absolute top-4 right-4 flex items-center gap-2 text-xs">
        <span className={`w-2 h-2 rounded-full ${serverOk === true ? 'bg-green-400' : serverOk === false ? 'bg-red-500' : 'bg-yellow-500'}`} />
        <span className="text-[#506080]">
          {serverOk === true ? 'VPS online' : serverOk === false ? 'VPS offline (modo local)' : 'Verificando VPS…'}
        </span>
      </div>

      <div className="w-full max-w-md px-4">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="text-2xl font-black tracking-widest text-[#50a0ff] mb-1">CINEFORGE</div>
          <div className="text-xs tracking-[0.4em] text-[#304060]">I·AI STUDIOS</div>
        </div>

        {screen === 'plans' ? (
          <PlansScreen
            selectedPlan={selectedPlan}
            onSelect={setSelectedPlan}
            onBack={() => setScreen('register')}
          />
        ) : (
          <div className="bg-[#0a0f1e] border border-[#1a2a40] rounded-xl p-6">
            {/* Tabs */}
            <div className="flex gap-1 mb-6 bg-black/40 rounded-lg p-1">
              {(['login', 'register'] as Screen[]).map(s => (
                <button
                  key={s}
                  onClick={() => { setScreen(s); setError('') }}
                  className={`flex-1 py-2 text-xs font-bold tracking-wider rounded-md transition-all ${
                    screen === s ? 'bg-[#1a3a5c] text-[#50a0ff]' : 'text-[#304060] hover:text-[#506080]'
                  }`}
                >
                  {s === 'login' ? 'ENTRAR' : 'CADASTRAR'}
                </button>
              ))}
            </div>

            {screen === 'login' ? (
              <form onSubmit={handleLogin} className="flex flex-col gap-4">
                <div>
                  <label className="text-xs text-[#506080] tracking-widest mb-1 block">E-MAIL</label>
                  <input className={inputCls} type="email" placeholder="seu@email.com"
                    value={email} onChange={e => setEmail(e.target.value)} required />
                </div>
                <div>
                  <label className="text-xs text-[#506080] tracking-widest mb-1 block">SENHA</label>
                  <input className={inputCls} type="password" placeholder="••••••••"
                    value={password} onChange={e => setPassword(e.target.value)} required />
                </div>
                {error && <p className="text-red-400 text-xs text-center">{error}</p>}
                <button className={btnCls} disabled={loading}>
                  {loading ? 'AUTENTICANDO…' : 'ENTRAR NO COCKPIT'}
                </button>
                <p className="text-center text-xs text-[#304060]">
                  Sem conta?{' '}
                  <button type="button" onClick={() => setScreen('register')}
                    className="text-[#50a0ff] hover:underline">
                    Cadastre-se grátis
                  </button>
                </p>
              </form>
            ) : (
              <form onSubmit={handleRegister} className="flex flex-col gap-4">
                <div>
                  <label className="text-xs text-[#506080] tracking-widest mb-1 block">NOME</label>
                  <input className={inputCls} type="text" placeholder="Seu nome"
                    value={name} onChange={e => setName(e.target.value)} required />
                </div>
                <div>
                  <label className="text-xs text-[#506080] tracking-widest mb-1 block">E-MAIL</label>
                  <input className={inputCls} type="email" placeholder="seu@email.com"
                    value={email} onChange={e => setEmail(e.target.value)} required />
                </div>
                <div>
                  <label className="text-xs text-[#506080] tracking-widest mb-1 block">SENHA</label>
                  <input className={inputCls} type="password" placeholder="Mínimo 8 caracteres"
                    value={password} onChange={e => setPassword(e.target.value)} required minLength={8} />
                </div>
                {/* Plano selecionado */}
                <div>
                  <label className="text-xs text-[#506080] tracking-widest mb-1 block">PLANO</label>
                  <div className="flex items-center justify-between bg-black/40 border border-[#1a3a5c] rounded px-3 py-2">
                    <span className="text-sm text-[#c0d8f0]">
                      {PLAN_LABELS[selectedPlan]?.label} — {PLAN_LABELS[selectedPlan]?.price}
                    </span>
                    <button type="button" onClick={() => setScreen('plans')}
                      className="text-xs text-[#50a0ff] hover:underline">
                      Mudar
                    </button>
                  </div>
                </div>
                {error && <p className="text-red-400 text-xs text-center">{error}</p>}
                <button className={btnCls} disabled={loading}>
                  {loading ? 'CRIANDO CONTA…' : 'CRIAR CONTA'}
                </button>
                <p className="text-center text-xs text-[#304060]">
                  Já tem conta?{' '}
                  <button type="button" onClick={() => setScreen('login')}
                    className="text-[#50a0ff] hover:underline">
                    Entrar
                  </button>
                </p>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function PlansScreen({
  selectedPlan,
  onSelect,
  onBack,
}: {
  selectedPlan: string
  onSelect: (p: string) => void
  onBack: () => void
}) {
  return (
    <div>
      <h2 className="text-center text-sm font-bold tracking-widest text-[#50a0ff] mb-4">
        ESCOLHA SEU PLANO
      </h2>
      <div className="grid grid-cols-2 gap-3 mb-4">
        {Object.entries(PLAN_LABELS).map(([key, info]) => (
          <button
            key={key}
            onClick={() => onSelect(key)}
            className={`rounded-lg p-3 text-left border transition-all ${
              selectedPlan === key
                ? 'border-[#50a0ff] bg-[#0d1e35]'
                : 'border-[#1a2a40] bg-[#0a0f1e] hover:border-[#2a4a6a]'
            }`}
          >
            <div className="text-xs font-bold text-[#50a0ff] mb-1">{info.label}</div>
            <div className="text-sm font-black text-white mb-2">{info.price}</div>
            {info.features.map(f => (
              <div key={f} className="text-[10px] text-[#506080] flex gap-1 items-start">
                <span className="text-[#50a0ff] mt-0.5">›</span> {f}
              </div>
            ))}
          </button>
        ))}
      </div>
      <button
        onClick={onBack}
        className="w-full py-2 rounded text-sm font-bold tracking-wider bg-[#50a0ff] hover:bg-[#70b8ff] text-black"
      >
        CONFIRMAR — {PLAN_LABELS[selectedPlan]?.label}
      </button>
    </div>
  )
}
