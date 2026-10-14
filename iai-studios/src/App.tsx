import { useState, useEffect, useRef } from 'react'
import Globe from './components/Globe'
import ModuleCard from './components/ModuleCard'
import AuthScreen from './AuthScreen'
import { useAuth } from './AuthContext'

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

const VPS_HOST = 'http://167.234.255.202:8765'

const VIDEO_MAIN = '/videos/CINEFORGE_OPTIMIZED.webm'

// ── Module action panels ────────────────────────────────────────────────────

function ModRoteiro({ onClose }: { onClose: () => void }) {
  const [topic, setTopic] = useState('')
  const [niche, setNiche] = useState('dark')
  const [minutes, setMinutes] = useState('8')
  const [status, setStatus] = useState('')
  const [result, setResult] = useState<Record<string, unknown> | null>(null)

  async function gerarRoteiro() {
    if (!topic.trim()) { setStatus('ERRO: INFORME O TÓPICO'); return }
    setStatus('⚡ SINCRONIZANDO COM VPS HERMES...')
    setResult(null)
    try {
      const r = await fetch(`${VPS_HOST}/gerar-roteiro`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, niche, duration_min: parseInt(minutes) }),
      })
      const data = await r.json()
      setResult(data)
      setStatus('✅ ROTEIRO GERADO COM SUCESSO')
    } catch (e) {
      setStatus(`❌ VPS OFFLINE — USE: python3 src/pipeline/01_scriptwriter.py "${topic}"`)
    }
  }

  return (
    <ModPanel title="ROTEIRO IA" onClose={onClose} badge="MOD.01">
      <Field label="TÓPICO DO VÍDEO">
        <input className="cf-input" value={topic} onChange={e => setTopic(e.target.value)}
          placeholder="Ex: serial killer no Brasil anos 90" />
      </Field>
      <div style={{ display: 'flex', gap: 16 }}>
        <Field label="NICHO">
          <select className="cf-input" value={niche} onChange={e => setNiche(e.target.value)}>
            <option value="dark">Dark / Crime</option>
            <option value="tech">Tech / IA</option>
            <option value="finance">Finanças</option>
            <option value="health">Saúde</option>
            <option value="education">Educação</option>
            <option value="entertainment">Entretenimento</option>
          </select>
        </Field>
        <Field label="DURAÇÃO (MIN)">
          <input className="cf-input" type="number" min="3" max="30" value={minutes}
            onChange={e => setMinutes(e.target.value)} style={{ width: 80 }} />
        </Field>
      </div>
      <button className="cf-btn" onClick={gerarRoteiro}>⚡ GERAR ROTEIRO</button>
      {status && <StatusLine text={status} />}
      {result && (
        <div className="cf-result">
          <div style={{ color: '#FFB800', marginBottom: 8 }}>
            📋 {String(result.titulo || 'Roteiro gerado')}
          </div>
          <div style={{ fontSize: 10, opacity: 0.7 }}>
            {Array.isArray(result.cenas) ? `${result.cenas.length} CENAS GERADAS` : JSON.stringify(result).slice(0, 200)}
          </div>
        </div>
      )}
    </ModPanel>
  )
}

function ModTrilha({ onClose }: { onClose: () => void }) {
  const [mood, setMood] = useState('tension')
  const [duration, setDuration] = useState('60')
  const [status, setStatus] = useState('')

  async function gerarTrilha() {
    setStatus('⚡ GERANDO TRILHA VIA HIGGSFIELD...')
    try {
      const r = await fetch(`${VPS_HOST}/gerar-trilha`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mood, duration_sec: parseInt(duration) }),
      })
      const data = await r.json()
      setStatus(data.url ? `✅ TRILHA: ${data.url}` : '✅ JOB INICIADO: ' + (data.job_id || ''))
    } catch {
      setStatus('❌ VPS OFFLINE — Conecte a Hermes para usar este módulo')
    }
  }

  return (
    <ModPanel title="TRILHA NEURAL" onClose={onClose} badge="MOD.02">
      <InfoBox>Gera trilha sonora cinematográfica via Higgsfield Audio API. Custo: ~$0.01/s.</InfoBox>
      <Field label="MOOD / ATMOSFERA">
        <select className="cf-input" value={mood} onChange={e => setMood(e.target.value)}>
          <option value="tension">Tensão / Suspense</option>
          <option value="epic">Épico / Grandioso</option>
          <option value="dark">Dark / Sombrio</option>
          <option value="emotional">Emocional</option>
          <option value="action">Ação</option>
          <option value="mystery">Mistério</option>
        </select>
      </Field>
      <Field label="DURAÇÃO (SEG)">
        <input className="cf-input" type="number" min="15" max="300" value={duration}
          onChange={e => setDuration(e.target.value)} style={{ width: 100 }} />
      </Field>
      <button className="cf-btn" onClick={gerarTrilha}>🎵 COMPOR TRILHA</button>
      {status && <StatusLine text={status} />}
    </ModPanel>
  )
}

function ModLegacy({ onClose }: { onClose: () => void }) {
  const [voiceName, setVoiceName] = useState('')
  const [text, setText] = useState('')
  const [status, setStatus] = useState('')

  async function clonarVoz() {
    if (!voiceName.trim()) { setStatus('ERRO: INFORME O NOME DA VOZ'); return }
    setStatus('🔬 SEQUENCIANDO DNA VOCAL...')
    try {
      const r = await fetch(`${VPS_HOST}/clonar-voz`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice_name: voiceName, test_text: text }),
      })
      const data = await r.json()
      setStatus(data.voice_id ? `✅ VOZ CLONADA: ${data.voice_id}` : '❌ ' + (data.error || 'Erro'))
    } catch {
      setStatus('❌ VPS OFFLINE — Conecte a Hermes para usar este módulo')
    }
  }

  return (
    <ModPanel title="LEGACY CLONING" onClose={onClose} badge="MOD.03">
      <InfoBox>Clone de voz via Higgsfield + ElevenLabs. Faça upload do áudio de referência na VPS primeiro.</InfoBox>
      <Field label="NOME DA VOZ">
        <input className="cf-input" value={voiceName} onChange={e => setVoiceName(e.target.value)}
          placeholder="Ex: locutor_masculino_br" />
      </Field>
      <Field label="TEXTO DE TESTE">
        <textarea className="cf-input" rows={3} value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Digite texto para testar a voz clonada..." />
      </Field>
      <div style={{ fontSize: 9, color: '#FFB800', marginBottom: 8 }}>
        📁 UPLOAD: scp audio.mp3 ubuntu@167.234.255.202:/tmp/voice_ref.mp3
      </div>
      <button className="cf-btn" onClick={clonarVoz}>🧬 CLONAR VOZ</button>
      {status && <StatusLine text={status} />}
    </ModPanel>
  )
}

function ModGames({ onClose }: { onClose: () => void }) {
  const [scenario, setScenario] = useState('')
  const [style, setStyle] = useState('cinematic')
  const [imgUrl, setImgUrl] = useState('')
  const [status, setStatus] = useState('')

  async function gerarBackground() {
    if (!scenario.trim()) { setStatus('ERRO: DESCREVA O CENÁRIO'); return }
    setStatus('🎨 GERANDO VIA POLLINATIONS.AI...')
    setImgUrl('')
    const prompt = encodeURIComponent(`${scenario}, ${style}, game background, highly detailed, 4K`)
    const url = `https://image.pollinations.ai/prompt/${prompt}?width=1920&height=1080&nologo=true&model=flux`
    setImgUrl(url)
    setStatus('✅ BACKGROUND GERADO')
  }

  return (
    <ModPanel title="GAMES UNIVERSE" onClose={onClose} badge="MOD.04">
      <InfoBox>Gera backgrounds cinematográficos via Pollinations.ai (gratuito, sem API key).</InfoBox>
      <Field label="DESCRIÇÃO DO CENÁRIO">
        <input className="cf-input" value={scenario} onChange={e => setScenario(e.target.value)}
          placeholder="Ex: cidade futurista noturna com neon" />
      </Field>
      <Field label="ESTILO VISUAL">
        <select className="cf-input" value={style} onChange={e => setStyle(e.target.value)}>
          <option value="cinematic">Cinematográfico</option>
          <option value="cyberpunk">Cyberpunk</option>
          <option value="realistic">Ultra-realista</option>
          <option value="dark fantasy">Dark Fantasy</option>
          <option value="sci-fi">Sci-Fi</option>
          <option value="noir">Noir</option>
        </select>
      </Field>
      <button className="cf-btn" onClick={gerarBackground}>🖼️ GERAR BACKGROUND</button>
      {status && <StatusLine text={status} />}
      {imgUrl && (
        <div style={{ marginTop: 12 }}>
          <img src={imgUrl} alt="background" style={{ width: '100%', maxHeight: 200, objectFit: 'cover', border: '1px solid rgba(0,255,65,0.3)' }} />
          <div style={{ fontSize: 9, marginTop: 4, color: '#00FF41' }}>
            <a href={imgUrl} target="_blank" rel="noopener noreferrer" style={{ color: '#00FF41' }}>↗ ABRIR ORIGINAL 1920×1080</a>
          </div>
        </div>
      )}
    </ModPanel>
  )
}

function ModInfluencers({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState('')
  const [persona, setPersona] = useState('')
  const [style, setStyle] = useState('realistic')
  const [status, setStatus] = useState('')

  async function criarAvatar() {
    if (!name.trim()) { setStatus('ERRO: INFORME O NOME DO AVATAR'); return }
    setStatus('🤖 PREPARANDO AVATAR VIA HIGGSFIELD...')
    try {
      const r = await fetch(`${VPS_HOST}/criar-avatar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, persona, style }),
      })
      const data = await r.json()
      setStatus(data.job_id ? `✅ AVATAR INICIADO: ${data.job_id}` : '❌ ' + (data.error || 'Erro'))
    } catch {
      setStatus('❌ VPS OFFLINE — Use Higgsfield.ai diretamente: higgsfield.ai')
    }
  }

  return (
    <ModPanel title="INFLUENCERS" onClose={onClose} badge="MOD.05">
      <InfoBox>Cria avatares IA autônomos via Higgsfield AI Influencer. Custo: ~$0.05–0.20/geração.</InfoBox>
      <Field label="NOME DO AVATAR">
        <input className="cf-input" value={name} onChange={e => setName(e.target.value)}
          placeholder="Ex: Marina_Dark_Host" />
      </Field>
      <Field label="PERSONA / PERSONALIDADE">
        <textarea className="cf-input" rows={3} value={persona}
          onChange={e => setPersona(e.target.value)}
          placeholder="Descreva aparência, personalidade e estilo de narração..." />
      </Field>
      <Field label="ESTILO VISUAL">
        <select className="cf-input" value={style} onChange={e => setStyle(e.target.value)}>
          <option value="realistic">Ultra-realista</option>
          <option value="cinematic">Cinematográfico</option>
          <option value="stylized">Estilizado</option>
        </select>
      </Field>
      <button className="cf-btn" onClick={criarAvatar}>👤 CRIAR AVATAR</button>
      {status && <StatusLine text={status} />}
    </ModPanel>
  )
}

function ModDNA({ onClose }: { onClose: () => void }) {
  const [channel, setChannel] = useState('')
  const [status, setStatus] = useState('')
  const [result, setResult] = useState<Record<string, unknown> | null>(null)

  async function analisarConcorrente() {
    if (!channel.trim()) { setStatus('ERRO: INFORME O CANAL OU TÓPICO'); return }
    setStatus('🔬 SEQUENCIANDO DNA DO CONCORRENTE...')
    setResult(null)
    try {
      const r = await fetch(`${VPS_HOST}/analisar-concorrente`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_url: channel }),
      })
      const data = await r.json()
      setResult(data)
      setStatus('✅ ANÁLISE COMPLETA')
    } catch {
      setStatus('❌ VPS OFFLINE — Execute: python3 src/pipeline/01_scriptwriter.py --help')
    }
  }

  return (
    <ModPanel title="DNA SEQUENCER" onClose={onClose} badge="MOD.06">
      <InfoBox>Analisa canais concorrentes via Gemini + Google Search grounding para extrair estratégias.</InfoBox>
      <Field label="CANAL DO YOUTUBE / TÓPICO">
        <input className="cf-input" value={channel} onChange={e => setChannel(e.target.value)}
          placeholder="Ex: @CanalCrime ou 'crimes reais brasil'" />
      </Field>
      <button className="cf-btn" onClick={analisarConcorrente}>🔬 ANALISAR DNA</button>
      {status && <StatusLine text={status} />}
      {result && (
        <div className="cf-result" style={{ fontSize: 10 }}>
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {JSON.stringify(result, null, 2).slice(0, 600)}...
          </pre>
        </div>
      )}
    </ModPanel>
  )
}

function ModStoryboard({ onClose }: { onClose: () => void }) {
  const [json, setJson] = useState('')
  const [scenes, setScenes] = useState<{ titulo: string; corpo: string }[]>([])
  const [status, setStatus] = useState('')

  function parsear() {
    try {
      const data = JSON.parse(json)
      const cenas = data.cenas || data
      if (Array.isArray(cenas)) {
        setScenes(cenas)
        setStatus(`✅ ${cenas.length} CENAS CARREGADAS`)
      } else {
        setStatus('❌ JSON inválido — espera array de cenas')
      }
    } catch {
      setStatus('❌ JSON inválido')
    }
  }

  return (
    <ModPanel title="STORYBOARD" onClose={onClose} badge="MOD.07">
      <InfoBox>Cole o JSON do roteiro (saída do módulo ROTEIRO IA) para visualizar o storyboard.</InfoBox>
      <Field label="JSON DO ROTEIRO">
        <textarea className="cf-input" rows={4} value={json} onChange={e => setJson(e.target.value)}
          placeholder='{"cenas": [{"titulo": "...", "corpo": "..."}]}' />
      </Field>
      <button className="cf-btn" onClick={parsear}>🎬 VISUALIZAR STORYBOARD</button>
      {status && <StatusLine text={status} />}
      {scenes.length > 0 && (
        <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 260, overflowY: 'auto' }}>
          {scenes.map((s, i) => (
            <div key={i} style={{ border: '1px solid rgba(0,255,65,0.3)', padding: '8px 12px', background: 'rgba(0,0,0,0.4)' }}>
              <div style={{ color: '#FFB800', fontSize: 10, marginBottom: 4 }}>CENA {i + 1}</div>
              <div style={{ color: '#fff', fontWeight: 900, fontSize: 12 }}>{s.titulo}</div>
              <div style={{ color: '#00FF41', fontSize: 10, marginTop: 4 }}>{s.corpo?.slice(0, 120)}...</div>
            </div>
          ))}
        </div>
      )}
    </ModPanel>
  )
}

function ModDublagem({ onClose }: { onClose: () => void }) {
  const [text, setText] = useState('')
  const [voice, setVoice] = useState('pt-BR-FranciscaNeural')
  const [status, setStatus] = useState('')
  const [audioUrl, setAudioUrl] = useState('')

  async function dublar() {
    if (!text.trim()) { setStatus('ERRO: INFORME O TEXTO'); return }
    setStatus('🎙️ GERANDO NARRAÇÃO VIA EDGE-TTS...')
    setAudioUrl('')
    try {
      const r = await fetch(`${VPS_HOST}/gerar-audio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice }),
      })
      const data = await r.json()
      if (data.url) {
        setAudioUrl(data.url)
        setStatus('✅ ÁUDIO GERADO')
      } else {
        setStatus('❌ ' + (data.error || 'Erro ao gerar áudio'))
      }
    } catch {
      setStatus('❌ VPS OFFLINE — Execute na Hermes: python3 -c "import edge_tts; ..."')
    }
  }

  return (
    <ModPanel title="DUBLAGEM AI" onClose={onClose} badge="MOD.08">
      <InfoBox>Narração em português via Microsoft Edge-TTS (gratuito, 300+ vozes).</InfoBox>
      <Field label="TEXTO PARA NARRAR">
        <textarea className="cf-input" rows={5} value={text} onChange={e => setText(e.target.value)}
          placeholder="Cole o texto da narração aqui..." />
      </Field>
      <Field label="VOZ">
        <select className="cf-input" value={voice} onChange={e => setVoice(e.target.value)}>
          <option value="pt-BR-FranciscaNeural">Francisca (Feminina BR)</option>
          <option value="pt-BR-AntonioNeural">Antônio (Masculino BR)</option>
          <option value="pt-BR-BrendaNeural">Brenda (Feminina BR)</option>
          <option value="pt-BR-DonatoNeural">Donato (Masculino BR)</option>
          <option value="pt-PT-FernandaNeural">Fernanda (Portugal)</option>
        </select>
      </Field>
      <button className="cf-btn" onClick={dublar}>🎙️ GERAR NARRAÇÃO</button>
      {status && <StatusLine text={status} />}
      {audioUrl && (
        <div style={{ marginTop: 12 }}>
          <audio controls src={audioUrl} style={{ width: '100%' }} />
          <a href={audioUrl} download style={{ color: '#00FF41', fontSize: 10 }}>↓ BAIXAR MP3</a>
        </div>
      )}
    </ModPanel>
  )
}

function ModEdicao({ onClose }: { onClose: () => void }) {
  const [topic, setTopic] = useState('')
  const [niche, setNiche] = useState('dark')
  const [useAI, setUseAI] = useState(true)
  const [status, setStatus] = useState('')
  const [jobId, setJobId] = useState('')
  const [videoUrl, setVideoUrl] = useState('')
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  function startPolling(id: string) {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const r = await fetch(`${VPS_HOST}/status-video/${id}`)
        const data = await r.json()
        if (data.status === 'done') {
          clearInterval(pollRef.current!)
          setVideoUrl(data.url || '')
          setStatus(`✅ VÍDEO PRONTO: ${data.filename || id}`)
        } else if (data.status === 'error') {
          clearInterval(pollRef.current!)
          setStatus(`❌ ERRO: ${data.error}`)
        } else {
          setStatus(`⏳ RENDERIZANDO... ${data.progress || ''}`)
        }
      } catch { /* VPS pode estar processando */ }
    }, 5000)
  }

  async function gerarVideo() {
    if (!topic.trim()) { setStatus('ERRO: INFORME O TÓPICO'); return }
    setStatus('⚡ DISPARANDO PIPELINE NA VPS HERMES...')
    setVideoUrl('')
    setJobId('')
    try {
      const r = await fetch(`${VPS_HOST}/gerar-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, niche, use_ai_images: useAI }),
      })
      const data = await r.json()
      if (data.job_id) {
        setJobId(data.job_id)
        setStatus(`⏳ JOB INICIADO: ${data.job_id} — verificando a cada 5s...`)
        startPolling(data.job_id)
      } else {
        setStatus('❌ ' + (data.error || 'Erro ao iniciar job'))
      }
    } catch {
      setStatus('❌ VPS HERMES OFFLINE\n\nExecute manualmente na Hermes:\npython3 tools/video_generator.py "' + topic + '" --teste')
    }
  }

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])

  return (
    <ModPanel title="EDIÇÃO TÁTICA" onClose={onClose} badge="MOD.09">
      <InfoBox>Pipeline completo: Gemini roteiro → Pollinations imagens → EdgeTTS áudio → MoviePy MP4</InfoBox>
      <Field label="TÓPICO DO VÍDEO">
        <input className="cf-input" value={topic} onChange={e => setTopic(e.target.value)}
          placeholder="Ex: O caso mais chocante do Brasil" />
      </Field>
      <Field label="NICHO">
        <select className="cf-input" value={niche} onChange={e => setNiche(e.target.value)}>
          <option value="dark">Dark / Crime</option>
          <option value="tech">Tech / IA</option>
          <option value="finance">Finanças</option>
          <option value="health">Saúde</option>
          <option value="education">Educação</option>
          <option value="entertainment">Entretenimento</option>
        </select>
      </Field>
      <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 10, color: '#00FF41', marginBottom: 12 }}>
        <input type="checkbox" checked={useAI} onChange={e => setUseAI(e.target.checked)}
          style={{ accentColor: '#00FF41' }} />
        IMAGENS IA VIA POLLINATIONS (gratuito — adiciona ~30s/cena)
      </label>
      <button className="cf-btn" onClick={gerarVideo} style={{ backgroundColor: 'rgba(0,255,65,0.1)' }}>
        🎬 GERAR VÍDEO COMPLETO
      </button>
      {status && (
        <div className="cf-result" style={{ whiteSpace: 'pre-wrap' }}>
          <StatusLine text={status} />
          {jobId && <div style={{ fontSize: 9, marginTop: 4, opacity: 0.6 }}>JOB_ID: {jobId}</div>}
        </div>
      )}
      {videoUrl && (
        <div style={{ marginTop: 12 }}>
          <video controls src={videoUrl} style={{ width: '100%', maxHeight: 200 }} />
          <a href={videoUrl} download style={{ color: '#00FF41', fontSize: 10, marginTop: 4, display: 'block' }}>
            ↓ BAIXAR MP4
          </a>
        </div>
      )}
    </ModPanel>
  )
}

function ModColorGrade({ onClose }: { onClose: () => void }) {
  const [preset, setPreset] = useState('dark_cinematic')
  const [bg, setBg] = useState('15,15,25')
  const [accent, setAccent] = useState('80,160,255')
  const [status, setStatus] = useState('')

  async function aplicarGrade() {
    setStatus('🎨 APLICANDO COLOR GRADE NA VPS...')
    try {
      const r = await fetch(`${VPS_HOST}/configurar-visual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preset, bg_color: bg, accent_color: accent }),
      })
      const data = await r.json()
      setStatus(data.ok ? '✅ CONFIGURAÇÕES SALVAS NA VPS' : '❌ ' + data.error)
    } catch {
      setStatus(`❌ VPS OFFLINE\n\nExporte como variáveis de ambiente:\nSLIDE_BG="${bg}"\nSLIDE_ACCENT="${accent}"`)
    }
  }

  const presets: Record<string, { bg: string; accent: string }> = {
    dark_cinematic: { bg: '15,15,25', accent: '80,160,255' },
    neon_crime: { bg: '5,0,15', accent: '255,0,100' },
    amber_thriller: { bg: '20,10,0', accent: '255,180,0' },
    green_matrix: { bg: '0,10,0', accent: '0,255,65' },
    blood_noir: { bg: '20,0,0', accent: '200,30,30' },
  }

  function applyPreset(p: string) {
    setPreset(p)
    if (presets[p]) { setBg(presets[p].bg); setAccent(presets[p].accent) }
  }

  const previewBg = `rgb(${bg})`
  const previewAccent = `rgb(${accent})`

  return (
    <ModPanel title="COLOR GRADE" onClose={onClose} badge="MOD.10">
      <InfoBox>Define paleta de cores dos slides do pipeline de vídeo. Persiste via variáveis na VPS.</InfoBox>
      <Field label="PRESET">
        <select className="cf-input" value={preset} onChange={e => applyPreset(e.target.value)}>
          <option value="dark_cinematic">Dark Cinematic (padrão)</option>
          <option value="neon_crime">Neon Crime</option>
          <option value="amber_thriller">Amber Thriller</option>
          <option value="green_matrix">Green Matrix</option>
          <option value="blood_noir">Blood Noir</option>
        </select>
      </Field>
      <div style={{ display: 'flex', gap: 16 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 9, color: '#00FF41', marginBottom: 4 }}>BG (R,G,B)</div>
          <input className="cf-input" value={bg} onChange={e => setBg(e.target.value)} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 9, color: '#00FF41', marginBottom: 4 }}>ACENTO (R,G,B)</div>
          <input className="cf-input" value={accent} onChange={e => setAccent(e.target.value)} />
        </div>
      </div>
      <div style={{ height: 40, background: previewBg, border: `2px solid ${previewAccent}`, marginTop: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, color: previewAccent }}>
        PREVIEW // SLIDE BACKGROUND
      </div>
      <div style={{ fontSize: 9, color: '#FFB800', marginTop: 8, fontFamily: 'monospace' }}>
        SLIDE_BG="{bg}" SLIDE_ACCENT="{accent}"
      </div>
      <button className="cf-btn" onClick={aplicarGrade} style={{ marginTop: 12 }}>🎨 APLICAR GRADE</button>
      {status && <StatusLine text={status} />}
    </ModPanel>
  )
}

function ModRender({ onClose }: { onClose: () => void }) {
  const [jobs, setJobs] = useState<{ id: string; status: string; topic: string; created: string }[]>([])
  const [status, setStatus] = useState('AGUARDANDO CONEXÃO...')

  async function carregarJobs() {
    setStatus('⏳ CONSULTANDO VPS HERMES...')
    try {
      const r = await fetch(`${VPS_HOST}/listar-jobs`)
      const data = await r.json()
      setJobs(data.jobs || [])
      setStatus(`✅ ${data.jobs?.length || 0} JOBS ENCONTRADOS`)
    } catch {
      setStatus('❌ VPS OFFLINE\n\nVerifique: ssh ubuntu@167.234.255.202\nls output/videos/')
    }
  }

  useEffect(() => { carregarJobs() }, [])

  const statusColor = (s: string) =>
    s === 'done' ? '#00FF41' : s === 'error' ? '#FF4444' : '#FFB800'

  return (
    <ModPanel title="RENDER 8K" onClose={onClose} badge="MOD.11">
      <InfoBox>Monitor de jobs de renderização na VPS Hermes. Refresh a cada clique.</InfoBox>
      <button className="cf-btn" onClick={carregarJobs}>🔄 ATUALIZAR JOBS</button>
      <StatusLine text={status} />
      <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 280, overflowY: 'auto' }}>
        {jobs.length === 0 && (
          <div style={{ fontSize: 10, opacity: 0.5, textAlign: 'center', padding: 20 }}>
            NENHUM JOB ENCONTRADO
          </div>
        )}
        {jobs.map((j) => (
          <div key={j.id} style={{ border: `1px solid ${statusColor(j.status)}`, padding: '8px 12px', background: 'rgba(0,0,0,0.4)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ color: statusColor(j.status), fontSize: 10 }}>● {j.status.toUpperCase()}</span>
              <span style={{ fontSize: 9, opacity: 0.5 }}>{j.created}</span>
            </div>
            <div style={{ color: '#fff', fontSize: 11 }}>{j.topic}</div>
            <div style={{ fontSize: 9, opacity: 0.5, fontFamily: 'monospace' }}>{j.id}</div>
          </div>
        ))}
      </div>
    </ModPanel>
  )
}

function ModDeploy({ onClose }: { onClose: () => void }) {
  const [videoFile, setVideoFile] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [platform, setPlatform] = useState('youtube')
  const [status, setStatus] = useState('')

  async function deployVideo() {
    if (!videoFile.trim() || !title.trim()) { setStatus('ERRO: INFORME ARQUIVO E TÍTULO'); return }
    setStatus('🚀 INICIANDO DEPLOY...')
    try {
      const r = await fetch(`${VPS_HOST}/deploy-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_file: videoFile, title, description, platform }),
      })
      const data = await r.json()
      setStatus(data.url ? `✅ PUBLICADO: ${data.url}` : '❌ ' + (data.error || 'Erro'))
    } catch {
      setStatus('❌ VPS OFFLINE\n\nPara deploy manual na Hermes:\nyoutube-upload --title "' + title + '" output/videos/' + videoFile)
    }
  }

  return (
    <ModPanel title="DEPLOY GLOBAL" onClose={onClose} badge="MOD.12">
      <InfoBox>Publica vídeos no YouTube, Google Drive e outras plataformas via rclone/youtube-upload na VPS.</InfoBox>
      <Field label="ARQUIVO DE VÍDEO (output/videos/)">
        <input className="cf-input" value={videoFile} onChange={e => setVideoFile(e.target.value)}
          placeholder="Ex: meu_video.mp4" />
      </Field>
      <Field label="TÍTULO DO VÍDEO">
        <input className="cf-input" value={title} onChange={e => setTitle(e.target.value)}
          placeholder="Título para publicação" />
      </Field>
      <Field label="DESCRIÇÃO">
        <textarea className="cf-input" rows={3} value={description} onChange={e => setDescription(e.target.value)}
          placeholder="Descrição, hashtags, links..." />
      </Field>
      <Field label="PLATAFORMA">
        <select className="cf-input" value={platform} onChange={e => setPlatform(e.target.value)}>
          <option value="youtube">YouTube</option>
          <option value="drive">Google Drive</option>
          <option value="both">YouTube + Drive</option>
        </select>
      </Field>
      <button className="cf-btn" onClick={deployVideo}>🚀 FAZER DEPLOY</button>
      {status && <StatusLine text={status} />}
    </ModPanel>
  )
}

// ── Reusable panel components ─────────────────────────────────────────────

function ModPanel({ title, badge, onClose, children }: {
  title: string; badge: string; onClose: () => void; children: React.ReactNode
}) {
  return (
    <div style={{ position: 'relative', zIndex: 10, height: '100%', display: 'flex', flexDirection: 'column', paddingTop: '3vh' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid rgba(0,255,65,0.4)', paddingBottom: 10, marginBottom: 20 }}>
        <div>
          <div style={{ fontSize: 9, color: '#00FF41', opacity: 0.6, letterSpacing: 4 }}>{badge} // MÓDULO ATIVO</div>
          <h2 style={{ fontSize: '3vw', fontWeight: 900, color: '#00FF41', WebkitTextStroke: '1px #fff', margin: '4px 0 0' }}>
            {title}
          </h2>
        </div>
        <button onClick={onClose} className="btn-neural" style={{ padding: '8px 24px', fontSize: 12 }}>✕ RETORNAR</button>
      </div>
      <div style={{ flex: 1, overflowY: 'auto', paddingRight: 8 }}>
        {children}
      </div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 9, color: '#00FF41', letterSpacing: 2, marginBottom: 4 }}>{label}</div>
      {children}
    </div>
  )
}

function InfoBox({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ border: '1px solid rgba(0,255,65,0.2)', padding: '8px 12px', fontSize: 10, color: '#FFB800', marginBottom: 16, background: 'rgba(255,184,0,0.03)' }}>
      ℹ️ {children}
    </div>
  )
}

function StatusLine({ text }: { text: string }) {
  const isError = text.startsWith('❌')
  const isOk = text.startsWith('✅')
  return (
    <div style={{
      fontFamily: 'monospace', fontSize: 10, padding: '8px 12px',
      border: `1px solid ${isError ? 'rgba(255,0,0,0.3)' : isOk ? 'rgba(0,255,65,0.3)' : 'rgba(255,184,0,0.3)'}`,
      color: isError ? '#FF6666' : isOk ? '#00FF41' : '#FFB800',
      background: 'rgba(0,0,0,0.5)', whiteSpace: 'pre-wrap', marginTop: 8,
    }}>
      {text}
    </div>
  )
}

// ── Module panel router ──────────────────────────────────────────────────

const MODULE_PANELS = [
  ModRoteiro, ModTrilha, ModLegacy, ModGames, ModInfluencers, ModDNA,
  ModStoryboard, ModDublagem, ModEdicao, ModColorGrade, ModRender, ModDeploy,
]

// ── Main App ──────────────────────────────────────────────────────────────

// ── User Badge ────────────────────────────────────────────────────────────────
function UserBadge() {
  const { user, logout } = useAuth()
  if (!user) return null
  const planColors: Record<string, string> = {
    free: '#506080', creator: '#50a0ff', pro: '#a0d080', studio: '#ffd060',
  }
  const color = planColors[user.plan] || '#506080'
  return (
    <div className="p-auto" style={{
      position: 'fixed', top: 12, right: 16, zIndex: 9999,
      display: 'flex', alignItems: 'center', gap: 8,
      background: 'rgba(0,0,0,0.7)', border: `1px solid ${color}40`,
      borderRadius: 8, padding: '4px 10px',
    }}>
      <span style={{ fontSize: 10, color, fontWeight: 900, letterSpacing: '0.1em' }}>
        {user.plan.toUpperCase()}
      </span>
      <span style={{ fontSize: 10, color: '#607090' }}>|</span>
      <span style={{ fontSize: 10, color: '#8090b0' }}>{user.name}</span>
      <button onClick={logout} style={{
        fontSize: 9, color: '#405060', cursor: 'pointer',
        background: 'none', border: 'none', fontFamily: 'inherit',
        letterSpacing: '0.1em', textTransform: 'uppercase',
      }}>sair</button>
    </div>
  )
}

export default function App() {
  const { user, loading } = useAuth()
  const [showAuth, setShowAuth] = useState(false)
  const [stage, setStage] = useState(0)
  const [activeModule, setActiveModule] = useState<number | null>(null)
  const [videoFrame, setVideoFrame] = useState(1)
  const rafRef = useRef(0)

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

  function openModule(idx: number) {
    setActiveModule(idx)
    setVideoFrame(1)
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

  const ActivePanel = activeModule !== null ? MODULE_PANELS[activeModule] : null

  return (
    <main className="cockpit-ultimate">
      {/* Auth overlay */}
      {showAuth && <AuthScreen onSuccess={() => setShowAuth(false)} />}
      {/* User badge (top-right) */}
      <UserBadge />
      {/* Login button when not authenticated */}
      {!user && !showAuth && (
        <button
          className="p-auto"
          onClick={() => setShowAuth(true)}
          style={{
            position: 'fixed', top: 12, right: 16, zIndex: 9998,
            background: 'rgba(0,0,0,0.7)', border: '1px solid #1a3a5c',
            borderRadius: 8, padding: '5px 14px', cursor: 'pointer',
            fontSize: 10, color: '#50a0ff', fontFamily: 'inherit',
            letterSpacing: '0.15em', textTransform: 'uppercase',
          }}
        >
          ENTRAR / CADASTRAR
        </button>
      )}
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

        .briefing-full { position: fixed; inset: 0; z-index: 500; display: flex; flex-direction: column; padding: 40px 80px; background: rgba(0,0,0,0.92); backdrop-filter: blur(4px); }
        .v-brief-bg { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; z-index: 1; filter: brightness(0.3); }
        .btn-neural { border: 2px solid #00FF41; color: #00FF41; padding: 12px 40px; font-size: 16px; font-weight: 900; cursor: pointer; background: transparent; letter-spacing: 4px; font-family: 'Orbitron', sans-serif; text-transform: uppercase; }
        .btn-neural:hover { background: rgba(0,255,65,0.1); }

        .cf-input { background: rgba(0,0,0,0.6); border: 1px solid rgba(0,255,65,0.4); color: #00FF41; padding: 8px 12px; font-family: monospace; font-size: 12px; width: 100%; box-sizing: border-box; outline: none; text-transform: none; }
        .cf-input:focus { border-color: #00FF41; }
        .cf-input option { background: #000; }
        .cf-btn { border: 2px solid #00FF41; color: #00FF41; padding: 10px 24px; font-size: 13px; font-weight: 900; cursor: pointer; background: rgba(0,255,65,0.05); letter-spacing: 3px; font-family: 'Orbitron', sans-serif; text-transform: uppercase; transition: 0.15s; width: 100%; }
        .cf-btn:hover { background: rgba(0,255,65,0.15); }
        .cf-result { background: rgba(0,0,0,0.5); border: 1px solid rgba(0,255,65,0.2); padding: 10px 14px; font-family: monospace; font-size: 11px; margin-top: 8px; }

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

        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: rgba(0,0,0,0.3); }
        ::-webkit-scrollbar-thumb { background: rgba(0,255,65,0.4); }
      `}</style>

      <div className="ui-root">
        {stage === 0 && (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }} className="p-auto">
            <button onClick={startInterface} className="btn-neural">
              INICIALIZAR INTERFACE
            </button>
          </div>
        )}

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

        {stage === 3 && !activeModule && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }} className="p-auto">
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '2px solid rgba(0,255,65,0.3)', paddingBottom: '10px' }}>
              <div style={{ fontSize: '13px', fontWeight: 900 }}>CINEFORGE_CORE // ONLINE</div>
              <div style={{ color: '#FFB800', fontWeight: 900 }}>PHASE 03 // COCKPIT</div>
              <button
                onClick={() => setStage(1)}
                style={{ color: 'red', border: '1px solid red', background: 'none', padding: '2px 8px', cursor: 'pointer', fontWeight: 900, fontFamily: 'inherit' }}
              >SAIR</button>
            </div>

            <div className="dashboard-grid">
              <div style={{ width: 340, display: 'flex', flexDirection: 'column', gap: 10 }}>
                {MODULES.slice(0, 6).map((m, i) => (
                  <ModuleCard key={i} name={m.name} hint={m.hint} index={i} side="left" onClick={() => openModule(i)} />
                ))}
              </div>

              <div style={{ position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%, -50%)', pointerEvents: 'none' }}>
                <Globe />
              </div>

              <div style={{ width: 340, display: 'flex', flexDirection: 'column', gap: 10 }}>
                {MODULES.slice(6, 12).map((m, i) => (
                  <ModuleCard key={i + 6} name={m.name} hint={m.hint} index={i + 6} side="right" onClick={() => openModule(i + 6)} />
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '2px solid rgba(0,255,65,0.3)', paddingTop: '10px', fontSize: '12px', fontWeight: 900 }}>
              <div>FPS <span>120</span></div>
              <div>RES 8K</div>
              <div>CPU <span>81%</span></div>
              <div>NET 12.4 TB/S</div>
            </div>
          </div>
        )}
      </div>

      {activeModule !== null && ActivePanel && (
        <div className="briefing-full p-auto">
          <video
            autoPlay
            playsInline
            loop
            className="v-brief-bg"
            src={`/videos/briefing/card${Math.min(activeModule + 1, 2)}/1.webm`}
          />
          <ActivePanel onClose={closeModule} />
        </div>
      )}
    </main>
  )
}
