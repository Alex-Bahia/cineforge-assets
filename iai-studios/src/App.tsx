import { useState, useEffect, useRef } from 'react'
import Globe from './components/Globe'
import ModuleCard from './components/ModuleCard'

declare global {
  interface Window {
    puter?: {
      auth: { isSignedIn: () => boolean; signIn: () => void }
      ai: { chat: (prompt: string, opts?: { model?: string }) => Promise<unknown> }
    }
  }
}

const MODULES = [
  { name: 'ROTEIRO IA',     hint: 'SCRIPTS EM LINGUAGEM FORMAL' },
  { name: 'TRILHA NEURAL',  hint: 'COMPOSIÇÃO MUSICAL ADAPTATIVA' },
  { name: 'LEGACY CLONING', hint: 'DNA DIGITAL E RECONSTRUÇÃO' },
  { name: 'GAMES UNIVERSE', hint: 'AMBIENTES VIRTUAL IA' },
  { name: 'INFLUENCERS',    hint: 'AVATARES AUTÔNOMOS' },
  { name: 'DNA SEQUENCER',  hint: 'MAPEAMENTO GENÉTICO' },
  { name: 'STORYBOARD',     hint: 'QUADROS TÁTICOS E RITMO' },
  { name: 'DUBLAGEM AI',    hint: 'EMOÇÃO + LIP-SYNC' },
  { name: 'EDIÇÃO TÁTICA',  hint: 'CORTES PREDITIVOS' },
  { name: 'COLOR GRADE',    hint: 'LUTS CINEMATOGRÁFICOS' },
  { name: 'RENDER 8K',      hint: 'ALTA GPU DEDICADA' },
  { name: 'DEPLOY GLOBAL',  hint: 'MÚLTIPLOS NODES' },
]

const VIDEO_MAIN = '/videos/CINEFORGE_OPTIMIZED.webm'

export default function App() {
  const [stage, setStage] = useState(0)         // 0=splash 1=intro 3=cockpit
  const [activeModule, setActiveModule] = useState<number | null>(null)
  const [videoFrame, setVideoFrame] = useState(1)
  const [aiText, setAiText] = useState('')
  const rafRef = useRef(0)

  // Controla vídeo de fundo conforme estágio
  useEffect(() => {
    const vid = document.getElementById('video-bg') as HTMLVideoElement | null
    if (!vid) return
    if (activeModule !== null) {
      vid.muted = true; vid.volume = 0
    } else if (stage > 0) {
      vid.muted = false; vid.volume = 1
    }
    function tick() {
      if (!activeModule) {
        if (stage === 3 && vid!.currentTime >= vid!.duration - 0.5) vid!.currentTime = 15
        if (stage === 1 && vid!.currentTime >= 8) vid!.currentTime = 0.1
      }
      rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [stage, activeModule])

  async function queryPuter(moduleName: string) {
    setAiText('SINCRO NEURAL EM CURSO...')
    if (!window.puter?.ai) return
    if (!window.puter.auth.isSignedIn()) {
      setAiText('AUTORIZE O LINK NEURAL PARA ACESSAR DADOS...')
      window.puter.auth.signIn()
      return
    }
    try {
      const res = await window.puter.ai.chat(
        `Aja como a IA tática Predator. Relatório técnico agressivo de 15 palavras sobre: ${moduleName}.`,
        { model: 'claude-3-5-sonnet' }
      )
      setAiText(String(res).toUpperCase())
    } catch {
      setAiText('ERRO DE PROCESSAMENTO // RECALIBRANDO...')
    }
  }

  function openModule(idx: number) {
    setActiveModule(idx)
    setVideoFrame(1)
    queryPuter(MODULES[idx].name)
  }

  function closeModule() {
    setActiveModule(null)
    setVideoFrame(1)
    const vid = document.getElementById('video-bg') as HTMLVideoElement | null
    if (vid) { vid.src = VIDEO_MAIN; vid.muted = false; vid.volume = 1; vid.currentTime = 15; vid.play() }
  }

  function startInterface() {
    setStage(1)
    const vid = document.getElementById('video-bg') as HTMLVideoElement | null
    if (vid) { vid.src = VIDEO_MAIN; vid.muted = false; vid.volume = 1; vid.play() }
  }

  function enterCockpit() {
    const vid = document.getElementById('video-bg') as HTMLVideoElement | null
    if (vid) { vid.currentTime = 8.1; vid.play() }
    setStage(3)
  }

  const modIdx = activeModule !== null ? activeModule + 1 : 0

  return (
    <main className="cockpit-ultimate">
      {/* ─── Estilos injetados (idênticos ao original) ─── */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Black+Ops+One&family=Orbitron:wght@900&display=swap');
        .cockpit-ultimate { position: fixed; inset: 0; color: #00FF41; font-family: 'Orbitron', sans-serif; text-transform: uppercase; overflow: hidden; }
        .ui-root { position: relative; z-index: 100; width: 100vw; height: 100vh; display: flex; flex-direction: column; padding: 15px 30px; pointer-events: none; }
        .p-auto { pointer-events: auto; }

        .hero-title { display: flex; align-items: baseline; justify-content: center; gap: 2vw; }
        .hero-i, .hero-studios { font-family: 'Black Ops One', cursive; font-size: 10vw; color: #fff; }
        .hero-ai { font-family: 'Black Ops One', cursive; font-size: 10vw; background: repeating-linear-gradient(90deg, #00FF41 0 8px, rgba(0,255,65,0.3) 8px 14px); -webkit-background-clip: text; background-clip: text; color: transparent; -webkit-text-stroke: 3px #FFFFFF; filter: drop-shadow(0 0 25px #00FF41); }

        .dashboard-grid { flex: 1; display: flex; justify-content: space-between; align-items: center; position: relative; margin: 5px 0; }

        .mod-card-system { border: 1px solid rgba(0,255,65,0.3); padding: 8px 12px; cursor: pointer; background: rgba(0,0,0,0.1); transition: 0.2s; }
        .mod-card-system:hover { border-color: #00FF41; background: rgba(0,255,65,0.05); }

        .mod-title-text { font-size: 18px; font-weight: 900; color: #FFFFFF; margin: 1px 0; text-shadow: 0 0 10px rgba(255,255,255,0.2); }
        .mod-hint-text { font-size: 8px; color: #00FF41; opacity: 0.7; }
        .mod-top-row { display: flex; justify-content: space-between; font-size: 9px; opacity: 0.55; margin-bottom: 2px; }
        .mod-id-tag { letter-spacing: 0.1em; }
        .mod-count-tag { letter-spacing: 0.1em; }
        .mod-visual-bar { height: 2px; background: rgba(0,255,65,0.2); margin-top: 4px; position: relative; overflow: hidden; }
        .mod-visual-bar::after { content:''; position: absolute; top:0; width: 45%; height:100%; background:#00FF41; }
        .bar-r::after { right: 0; }
        .bar-l::after { left: 0; }

        .briefing-full { position: fixed; inset: 0; z-index: 500; display: flex; flex-direction: column; padding: 40px 60px; background: #000; }
        .v-brief-bg { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; z-index: 1; filter: brightness(1.2); }
        .btn-neural { border: 2px solid #00FF41; color: #00FF41; padding: 12px 40px; font-size: 16px; font-weight: 900; cursor: pointer; background: transparent; letter-spacing: 4px; font-family: 'Orbitron', sans-serif; text-transform: uppercase; }
        .btn-neural:hover { background: rgba(0,255,65,0.1); }

        .vibrate-max { animation: v-max 0.03s infinite; }
        @keyframes v-max {
          0%   { transform: translate(0,0); }
          25%  { transform: translate(-4px,2px); }
          50%  { transform: translate(4px,-2px); }
          75%  { transform: translate(-2px,-4px); }
          100% { transform: translate(0,0); }
        }
        .txt-r { text-align: right; }
        .txt-l { text-align: left; }
      `}</style>

      <div className="ui-root">
        {/* ── Stage 0: Splash ─────────────────────────────────────── */}
        {stage === 0 && (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }} className="p-auto">
            <button onClick={startInterface} className="btn-neural">
              INICIALIZAR INTERFACE
            </button>
          </div>
        )}

        {/* ── Stage 1: Hero title ──────────────────────────────────── */}
        {stage === 1 && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }} className="p-auto">
            <div className="hero-title vibrate-max">
              <span className="hero-i">I</span>
              <span className="hero-ai">AI</span>
              <span className="hero-studios">STUDIOS</span>
            </div>
            <p style={{ color: '#FFB800', fontStyle: 'italic', fontWeight: 900, letterSpacing: '0.8em', fontSize: '1.2vw', marginTop: '15px' }}>
              FORJANDO O CINEMA DO FUTURO
            </p>
            <button onClick={enterCockpit} className="btn-neural" style={{ marginTop: '35px' }}>
              ▶ INICIAR LINK NEURAL
            </button>
          </div>
        )}

        {/* ── Stage 3: Cockpit ─────────────────────────────────────── */}
        {stage === 3 && !activeModule && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }} className="p-auto">
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '2px solid rgba(0,255,65,0.3)', paddingBottom: '10px' }}>
              <div style={{ fontSize: '13px', fontWeight: 900 }}>CINEFORGE_CORE // ONLINE</div>
              <div style={{ color: '#FFB800', fontWeight: 900 }}>PHASE 03 // COCKPIT</div>
              <button
                onClick={() => setStage(1)}
                style={{ color: 'red', border: '1px solid red', background: 'none', padding: '2px 8px', cursor: 'pointer', fontWeight: 900, fontFamily: 'inherit' }}
              >SAIR</button>
            </div>

            {/* Dashboard */}
            <div className="dashboard-grid">
              {/* Left modules */}
              <div style={{ width: 340, display: 'flex', flexDirection: 'column', gap: 10 }}>
                {MODULES.slice(0, 6).map((m, i) => (
                  <ModuleCard key={i} name={m.name} hint={m.hint} index={i} side="left" onClick={() => openModule(i)} />
                ))}
              </div>

              {/* Center globe */}
              <div style={{ position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%, -50%)', pointerEvents: 'none' }}>
                <Globe />
              </div>

              {/* Right modules */}
              <div style={{ width: 340, display: 'flex', flexDirection: 'column', gap: 10 }}>
                {MODULES.slice(6, 12).map((m, i) => (
                  <ModuleCard key={i + 6} name={m.name} hint={m.hint} index={i + 6} side="right" onClick={() => openModule(i + 6)} />
                ))}
              </div>
            </div>

            {/* Footer */}
            <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '2px solid rgba(0,255,65,0.3)', paddingTop: '10px', fontSize: '12px', fontWeight: 900 }}>
              <div>FPS <span>120</span></div>
              <div>RES 8K</div>
              <div>CPU <span>81%</span></div>
              <div>NET 12.4 TB/S</div>
            </div>
          </div>
        )}
      </div>

      {/* ── Briefing overlay ────────────────────────────────────────── */}
      {activeModule !== null && (
        <div className="briefing-full p-auto">
          <video
            autoPlay
            playsInline
            loop={modIdx > 2}
            className="v-brief-bg"
            src={modIdx <= 2 ? `/videos/briefing/card${modIdx}/${videoFrame}.webm` : `/videos/briefing/card${modIdx}/1.webm`}
            onEnded={() => { if (modIdx <= 2 && videoFrame < 6) setVideoFrame(v => v + 1) }}
          />
          <div style={{ position: 'relative', zIndex: 10, borderLeft: '15px solid #00FF41', paddingLeft: '30px', marginTop: '5vh' }}>
            <p style={{ fontSize: '12px', color: '#fff', opacity: 0.6, letterSpacing: '4px' }}>SISTEMA_BRIEFING_ATIVO</p>
            <h2 style={{ fontSize: '4vw', fontWeight: 900, color: '#00FF41', WebkitTextStroke: '1px #fff' }}>
              {MODULES[activeModule].name}
            </h2>
            <div style={{ marginTop: 15, color: '#00FF41', fontFamily: 'monospace', fontSize: '1.2vw' }}>
              {' > '} {aiText}
            </div>
            <button onClick={closeModule} className="btn-neural" style={{ marginTop: 40 }}>
              RETORNAR
            </button>
          </div>
        </div>
      )}
    </main>
  )
}
