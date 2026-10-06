import { memo, useRef, useEffect } from 'react'
import {
  geoOrthographic,
  geoPath,
  geoGraticule,
} from 'd3-geo'
import { feature } from 'topojson-client'
import type { Topology } from 'topojson-specification'

// ─── Tipos declarados localmente para evitar deps de @types ───────────────────
declare global {
  interface Window {
    AudioContext: typeof AudioContext
    webkitAudioContext: typeof AudioContext
  }
}

interface Ship {
  da: number; dd: number; sz: number; glow: number
  trail: { x: number; y: number }[]
  x: number; y: number
}

class Formation {
  id: number; ang: number; dist: number; ships: Ship[]
  constructor(id: number, ang: number) {
    this.id = id
    this.ang = ang
    this.dist = 248 * (0.45 + id * 0.18)
    this.ships = Array.from({ length: 5 }, (_, t) => ({
      da: (t - 2) * 0.068,
      dd: t % 2 * 15 - (t === 2 ? 5 : 0),
      sz: t === 2 ? 6 : 4.6,
      glow: 0, trail: [], x: 0, y: 0,
    }))
  }
  update(dt: number) {
    this.dist -= 22 * dt
    if (this.dist < -22) this.dist = 248 * 0.94
    this.ships.forEach(s => {
      if (s.glow > 0) s.glow -= dt
      const n = Math.max(0, this.dist + s.dd)
      s.x = 280 + Math.cos(this.ang + s.da) * n
      s.y = 280 + Math.sin(this.ang + s.da) * n
      s.trail.push({ x: s.x, y: s.y })
      if (s.trail.length > 9) s.trail.shift()
    })
  }
  tryGlow(idx: number) {
    const s = this.ships[idx]
    if (!s || s.glow > 0) return false
    s.glow = 0.58; return true
  }
  draw(ctx: CanvasRenderingContext2D, alpha: number) {
    if (this.dist > 4 && this.dist < 248 * 0.97) {
      ctx.save()
      ctx.globalAlpha = 0.1 * alpha
      ctx.strokeStyle = this.ships.some(s => s.glow > 0) ? '#00ff88' : '#ff2200'
      ctx.lineWidth = 0.4
      ctx.setLineDash([3, 6])
      ctx.beginPath()
      this.ships.forEach((s, i) => i === 0 ? ctx.moveTo(s.x, s.y) : ctx.lineTo(s.x, s.y))
      ctx.stroke()
      ctx.setLineDash([])
      ctx.restore()
    }
    this.ships.forEach(s => {
      s.trail.forEach((p, r) => {
        ctx.save()
        ctx.globalAlpha = r / s.trail.length * 0.16 * alpha
        ctx.fillStyle = s.glow > 0 ? '#00ff88' : '#ff2200'
        ctx.beginPath(); ctx.arc(p.x, p.y, 1, 0, Math.PI * 2); ctx.fill()
        ctx.restore()
      })
      if (this.dist > -12 && this.dist < 248) drawShip(ctx, s.x, s.y, s.sz, s.glow > 0, alpha)
    })
  }
}

function drawShip(ctx: CanvasRenderingContext2D, x: number, y: number, n: number, green: boolean, alpha: number) {
  ctx.save(); ctx.translate(x, y)
  const a = green ? '#00ff88' : '#ff4400'
  const b = green ? '#88ffcc' : '#ffaa44'
  if (green) {
    ctx.globalAlpha = 0.22 * alpha; ctx.strokeStyle = '#00ff88'; ctx.lineWidth = 1.2
    ctx.beginPath(); ctx.arc(0, 0, n * 3, 0, Math.PI * 2); ctx.stroke()
    ctx.globalAlpha = 0.08 * alpha
    ctx.beginPath(); ctx.arc(0, 0, n * 4.8, 0, Math.PI * 2); ctx.stroke()
  }
  ctx.globalAlpha = (green ? 0.14 : 0.08) * alpha
  const g1 = ctx.createRadialGradient(0, n * 0.7, 0, 0, n * 0.7, n * 1.7)
  g1.addColorStop(0, green ? 'rgba(0,255,100,0.5)' : 'rgba(255,80,0,0.4)')
  g1.addColorStop(1, 'rgba(0,0,0,0)')
  ctx.fillStyle = g1; ctx.beginPath(); ctx.ellipse(0, n * 0.55, n * 1.8, n * 0.72, 0, 0, Math.PI * 2); ctx.fill()
  ctx.globalAlpha = 0.88 * alpha
  ctx.strokeStyle = green ? '#00ffaa' : '#ff6600'; ctx.lineWidth = n * 0.17
  ctx.beginPath(); ctx.ellipse(0, n * 0.07, n * 1.6, n * 0.37, 0, 0, Math.PI * 2); ctx.stroke()
  ctx.globalAlpha = alpha
  const g2 = ctx.createLinearGradient(0, -n * 0.2, 0, n * 0.52)
  if (green) {
    g2.addColorStop(0, '#003322'); g2.addColorStop(0.4, '#00aa55'); g2.addColorStop(1, '#001108')
  } else {
    g2.addColorStop(0, '#7a1a00'); g2.addColorStop(0.4, '#cc2200'); g2.addColorStop(1, '#180400')
  }
  ctx.fillStyle = g2; ctx.beginPath(); ctx.ellipse(0, n * 0.14, n * 1.48, n * 0.43, 0, 0, Math.PI * 2); ctx.fill()
  ctx.globalAlpha = 0.38 * alpha; ctx.strokeStyle = a; ctx.lineWidth = 0.6
  ctx.beginPath(); ctx.ellipse(0, n * 0.1, n * 0.92, n * 0.23, 0, 0, Math.PI * 2); ctx.stroke()
  const t = Date.now() * 0.02
  ;[-0.72, -0.36, 0, 0.36, 0.72].forEach((e, i) => {
    ctx.globalAlpha = (green ? 0.6 + Math.sin(t + i * 1.3) * 0.4 : 0.65) * (green ? 0.95 : 0.55) * alpha
    ctx.fillStyle = b; ctx.beginPath(); ctx.arc(n * e, n * 0.23, n * 0.19, 0, Math.PI * 2); ctx.fill()
  })
  ctx.globalAlpha = 0.82 * alpha
  const g3 = ctx.createRadialGradient(-n * 0.22, -n * 0.5, 0, 0, -n * 0.18, n * 0.93)
  g3.addColorStop(0, green ? 'rgba(140,255,190,0.8)' : 'rgba(255,180,90,0.7)')
  g3.addColorStop(0.5, green ? 'rgba(0,200,120,0.65)' : 'rgba(255,130,50,0.6)')
  g3.addColorStop(1, green ? 'rgba(0,60,30,0.5)' : 'rgba(70,12,0,0.5)')
  ctx.fillStyle = g3
  ctx.beginPath()
  ctx.moveTo(-n * 0.57, n * 0.04)
  ctx.bezierCurveTo(-n * 0.57, -n * 0.44, -n * 0.31, -n * 0.98, 0, -n * 0.98)
  ctx.bezierCurveTo(n * 0.31, -n * 0.98, n * 0.57, -n * 0.44, n * 0.57, n * 0.04)
  ctx.closePath(); ctx.fill()
  ctx.globalAlpha = 0.24 * alpha
  ctx.fillStyle = green ? 'rgba(180,255,220,0.6)' : 'rgba(255,200,140,0.5)'
  ctx.beginPath()
  ctx.moveTo(-n * 0.27, 0)
  ctx.bezierCurveTo(-n * 0.31, -n * 0.36, -n * 0.17, -n * 0.76, n * 0.02, -n * 0.76)
  ctx.bezierCurveTo(n * 0.18, -n * 0.76, n * 0.14, -n * 0.36, n * 0.06, 0)
  ctx.closePath(); ctx.fill()
  ctx.restore()
}

function drawCorners(ctx: CanvasRenderingContext2D, t: number, alpha: number) {
  ctx.save(); ctx.strokeStyle = '#ff2200'; ctx.lineWidth = 1.2; ctx.globalAlpha = 0.55 * alpha
  ;[[3, 3, 1, 1], [557, 3, -1, 1], [3, 557, 1, -1], [557, 557, -1, -1]].forEach(([x, y, dx, dy]) => {
    ctx.beginPath(); ctx.moveTo(x, y + dy * 64); ctx.lineTo(x, y); ctx.lineTo(x + dx * 64, y); ctx.stroke()
  })
  ctx.restore()
  drawMiniRadar(ctx, 7, 7, 54, t * 1.7, alpha)
  drawMiniRadar(ctx, 499, 7, 54, t * 1.3, alpha)
  drawWave(ctx, 7, 499, 54, t, alpha)
  drawBars(ctx, 499, 499, 54, t, alpha)
}

function drawMiniRadar(ctx: CanvasRenderingContext2D, x: number, y: number, n: number, r: number, alpha: number) {
  const cx = x + n / 2, cy = y + n / 2, rad = n / 2 - 2
  ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, rad, 0, Math.PI * 2); ctx.clip()
  ;[0.33, 0.66, 1].forEach(s => {
    ctx.globalAlpha = 0.2 * alpha; ctx.strokeStyle = '#ff2200'; ctx.lineWidth = 0.4
    ctx.beginPath(); ctx.arc(cx, cy, rad * s, 0, Math.PI * 2); ctx.stroke()
  })
  ctx.globalAlpha = 0.12 * alpha; ctx.strokeStyle = '#ff1100'; ctx.lineWidth = 0.3
  ctx.beginPath(); ctx.moveTo(cx - rad, cy); ctx.lineTo(cx + rad, cy); ctx.stroke()
  ctx.beginPath(); ctx.moveTo(cx, cy - rad); ctx.lineTo(cx, cy + rad); ctx.stroke()
  ctx.globalAlpha = 0.18 * alpha; ctx.beginPath(); ctx.moveTo(cx, cy)
  ctx.arc(cx, cy, rad, r - Math.PI / 3, r); ctx.closePath()
  ctx.fillStyle = 'rgba(255,40,0,0.25)'; ctx.fill()
  ctx.globalAlpha = 0.85 * alpha; ctx.strokeStyle = '#ff4400'; ctx.lineWidth = 0.9
  ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(r) * rad, cy + Math.sin(r) * rad); ctx.stroke()
  if (Math.sin(r * 6.3 + cx * 0.1) > 0.72) {
    ctx.globalAlpha = 0.9 * alpha; ctx.fillStyle = '#ff6600'
    ctx.beginPath(); ctx.arc(cx + Math.cos(r * 2.1) * rad * 0.45, cy + Math.sin(r * 3.3) * rad * 0.5, 1.8, 0, Math.PI * 2); ctx.fill()
  }
  ctx.restore()
  ctx.save(); ctx.globalAlpha = 0.4 * alpha; ctx.strokeStyle = '#ff2200'; ctx.lineWidth = 0.5
  ctx.beginPath(); ctx.arc(cx, cy, rad, 0, Math.PI * 2); ctx.stroke(); ctx.restore()
}

function drawWave(ctx: CanvasRenderingContext2D, x: number, y: number, n: number, r: number, alpha: number) {
  ctx.save(); ctx.globalAlpha = 0.75 * alpha; ctx.strokeStyle = '#ff3300'; ctx.lineWidth = 0.9
  ctx.beginPath()
  for (let i = 0; i <= n - 4; i++) {
    const ay = y + n / 2 + Math.sin(i / 5.5 + r * 3.2) * 9 + Math.sin(i / 3 + r * 5.1) * 4 + Math.sin(i / 11 + r * 1.4) * 5
    i === 0 ? ctx.moveTo(x + 2 + i, ay) : ctx.lineTo(x + 2 + i, ay)
  }
  ctx.stroke()
  ctx.globalAlpha = 0.4 * alpha; ctx.fillStyle = '#ff1a00'; ctx.font = '5px monospace'
  ctx.fillText('AUDIO', x + 8, y + n - 2); ctx.restore()
}

function drawBars(ctx: CanvasRenderingContext2D, x: number, y: number, n: number, r: number, alpha: number) {
  ctx.save()
  const bw = (n - 10) / 7 - 1
  for (let i = 0; i < 7; i++) {
    const h = Math.abs(Math.sin(r * 1.8 + i * 1.1 + Math.cos(r * 0.7 + i))) * n * 0.72 + 4
    const bx = x + 5 + (bw + 1) * i, by = y + n - 4 - h
    ctx.globalAlpha = 0.8 * alpha
    const g = ctx.createLinearGradient(0, by, 0, by + h)
    g.addColorStop(0, '#ff5500'); g.addColorStop(1, '#660000')
    ctx.fillStyle = g; ctx.fillRect(bx, by, bw, h)
  }
  ctx.globalAlpha = 0.4 * alpha; ctx.fillStyle = '#ff1a00'; ctx.font = '5px monospace'
  ctx.fillText('SIGNAL', x + 5, y + n - 2); ctx.restore()
}

function drawGrid(ctx: CanvasRenderingContext2D, alpha: number) {
  ctx.save()
  ctx.globalAlpha = 0.13 * alpha; ctx.strokeStyle = '#ff1100'; ctx.lineWidth = 0.3
  for (let a = 0; a < 360; a += 10) {
    const rad = a * Math.PI / 180
    ctx.beginPath(); ctx.moveTo(280, 280); ctx.lineTo(280 + Math.cos(rad) * 248, 280 + Math.sin(rad) * 248); ctx.stroke()
  }
  for (let t = 0; t < 360; t += 5) {
    const rad = (t - 90) * Math.PI / 180
    const len = t % 30 === 0 ? 13 : t % 10 === 0 ? 7 : 4
    ctx.globalAlpha = (t % 30 === 0 ? 0.68 : 0.28) * alpha
    ctx.strokeStyle = '#ff2200'; ctx.lineWidth = t % 30 === 0 ? 0.8 : 0.35
    ctx.beginPath()
    ctx.moveTo(280 + Math.cos(rad) * 249, 280 + Math.sin(rad) * 249)
    ctx.lineTo(280 + Math.cos(rad) * (248 + len), 280 + Math.sin(rad) * (248 + len))
    ctx.stroke()
  }
  ctx.globalAlpha = 0.72 * alpha; ctx.fillStyle = '#ff3300'; ctx.font = 'bold 8px monospace'
  for (let a = 0; a < 360; a += 30) {
    const rad = (a - 90) * Math.PI / 180
    ctx.fillText(String(a).padStart(3, '0'), 280 + Math.cos(rad) * 267 - 8, 280 + Math.sin(rad) * 267 + 3)
  }
  ctx.globalAlpha = 0.92 * alpha; ctx.fillStyle = '#ff5500'; ctx.font = 'bold 11px monospace'
  ;['N', 'E', 'S', 'W'].forEach((lbl, i) => {
    const rad = (i * 90 - 90) * Math.PI / 180
    ctx.fillText(lbl, 280 + Math.cos(rad) * 226 - 5, 280 + Math.sin(rad) * 226 + 4)
  })
  ctx.globalAlpha = alpha; ctx.fillStyle = '#ff6600'; ctx.beginPath(); ctx.arc(280, 280, 3, 0, Math.PI * 2); ctx.fill()
  ctx.restore()
}

function drawRings(ctx: CanvasRenderingContext2D, alpha: number) {
  ctx.save()
  ;[1, 0.75, 0.5, 0.25].forEach(f => {
    ctx.beginPath(); ctx.arc(280, 280, 248 * f, 0, Math.PI * 2)
    ctx.strokeStyle = '#ff2200'; ctx.lineWidth = f === 1 ? 1.8 : 0.5
    ctx.globalAlpha = (f === 1 ? 0.82 : 0.26) * alpha; ctx.stroke()
  })
  ctx.restore()
  drawGrid(ctx, alpha)
}

function easeInOut(t: number): number {
  const c = t % 11.2
  if (c < 3) return c / 3
  if (c < 7) return 1
  if (c < 10) return 1 - (c - 7) / 3
  return 0
}

function angleDiff(a: number, b: number): number {
  let d = ((a - b) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2)
  if (d > Math.PI) d -= Math.PI * 2
  return Math.abs(d)
}

interface GlobeProps { active?: boolean }

export default memo(function Globe({ active = true }: GlobeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const rafRef = useRef(0)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const lastPingRef = useRef(0)
  const timeAccRef = useRef(0)

  useEffect(() => {
    if (!active) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    function initAudio() {
      const AC = window.AudioContext ?? window.webkitAudioContext
      if (!audioCtxRef.current && AC) audioCtxRef.current = new AC()
      audioCtxRef.current?.resume()
    }
    canvas.addEventListener('click', initAudio, { once: true })

    function ping(freq: number) {
      const ac = audioCtxRef.current
      if (!ac) return
      const now = ac.currentTime
      if (now - lastPingRef.current < 0.1) return
      lastPingRef.current = now
      const osc = ac.createOscillator(), gain = ac.createGain()
      osc.connect(gain); gain.connect(ac.destination)
      osc.frequency.value = freq; osc.type = 'sine'
      gain.setValueAtTime(0.18, now)
      gain.exponentialRampToValueAtTime(0.001, now + 0.12)
      osc.start(now); osc.stop(now + 0.12)
    }

    const proj = geoOrthographic().center([10, 10]).scale(248 / Math.PI * 1.02).translate([280, 280])
    const path = geoPath(proj, ctx)
    const graticule = geoGraticule().step([20, 20])()

    let worldData: { type: string; features: unknown[] } | null = null
    let worldLoaded = false

    const controller = new AbortController()
    fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json', { signal: controller.signal })
      .then(r => r.json())
      .then((topo: Topology) => {
        const f = feature(topo, (topo.objects as Record<string, unknown>).countries as Parameters<typeof feature>[1])
        if (f.type === 'FeatureCollection') { worldData = f as unknown as typeof worldData; worldLoaded = true }
      }).catch(() => {})

    const formations = [
      new Formation(0, -Math.PI / 2 + 0.04),
      new Formation(1, Math.PI / 2 - 0.04),
      new Formation(2, Math.PI + 0.04),
      new Formation(3, -0.04),
    ]

    let globalT = 0
    let sweepAngle = -Math.PI / 2
    const sweepSpeed = Math.PI * 2 / 4.5
    const pinged = new Set<string>()
    let prevTime = performance.now()

    function frame(now: number) {
      const dt = Math.min((now - prevTime) / 1000, 0.05)
      prevTime = now
      timeAccRef.current += dt
      globalT += dt
      const alpha = easeInOut(globalT)

      ctx.clearRect(0, 0, 560, 560)
      if (alpha < 0.01) { rafRef.current = requestAnimationFrame(frame); return }

      drawCorners(ctx, timeAccRef.current, alpha)

      ctx.save()
      ctx.beginPath(); ctx.arc(280, 280, 248, 0, Math.PI * 2); ctx.clip()

      // world map
      if (worldLoaded && worldData && path) {
        ctx.save()
        ctx.globalAlpha = 0.07 * alpha; ctx.strokeStyle = '#ff1100'; ctx.lineWidth = 0.3
        ctx.beginPath(); path(graticule); ctx.stroke()
        worldData.features.forEach((f: unknown) => {
          ctx.save()
          ctx.globalAlpha = 0.25 * alpha; ctx.fillStyle = 'rgba(255,40,0,0.3)'
          ctx.beginPath(); path(f as Parameters<typeof path>[0]); ctx.fill()
          ctx.globalAlpha = 0.68 * alpha; ctx.strokeStyle = '#ff3300'; ctx.lineWidth = 0.75
          ctx.beginPath(); path(f as Parameters<typeof path>[0]); ctx.stroke()
          ctx.restore()
        })
        ctx.restore()
      }

      drawRings(ctx, alpha)

      sweepAngle += sweepSpeed * dt
      if (sweepAngle > Math.PI * 1.5) { sweepAngle -= Math.PI * 2; pinged.clear() }

      formations.forEach(f => {
        f.update(dt)
        f.ships.forEach((s, i) => {
          const ang = Math.atan2(s.y - 280, s.x - 280)
          const key = `${f.id}_${i}`
          if (angleDiff(sweepAngle, ang) < 0.22 && !pinged.has(key) && f.dist > 0 && f.dist < 248) {
            pinged.add(key)
            if (f.tryGlow(i)) ping(700 + Math.random() * 500)
          }
        })
      })

      // sweep gradient
      ctx.save()
      ctx.beginPath(); ctx.moveTo(280, 280)
      ctx.arc(280, 280, 248, sweepAngle - Math.PI / 5, sweepAngle); ctx.closePath()
      const sg = ctx.createLinearGradient(280, 280, 280 + Math.cos(sweepAngle) * 248, 280 + Math.sin(sweepAngle) * 248)
      sg.addColorStop(0, 'rgba(255,30,0,0)'); sg.addColorStop(1, `rgba(255,30,0,${0.22 * alpha})`)
      ctx.globalAlpha = 0.9; ctx.fillStyle = sg; ctx.fill()
      ctx.restore()

      // sweep line
      ctx.save()
      ctx.globalAlpha = 0.95 * alpha; ctx.strokeStyle = '#ff4400'; ctx.lineWidth = 1.6
      ctx.beginPath(); ctx.moveTo(280, 280); ctx.lineTo(280 + Math.cos(sweepAngle) * 248, 280 + Math.sin(sweepAngle) * 248); ctx.stroke()
      ctx.restore()

      formations.forEach(f => f.draw(ctx, alpha))
      ctx.restore()

      ctx.save(); ctx.strokeStyle = '#ff2200'; ctx.lineWidth = 2; ctx.globalAlpha = 0.88 * alpha
      ctx.beginPath(); ctx.arc(280, 280, 248, 0, Math.PI * 2); ctx.stroke(); ctx.restore()

      rafRef.current = requestAnimationFrame(frame)
    }

    rafRef.current = requestAnimationFrame(frame)

    return () => {
      cancelAnimationFrame(rafRef.current)
      canvas.removeEventListener('click', initAudio)
      controller.abort()
    }
  }, [active])

  return (
    <canvas
      ref={canvasRef}
      width={560}
      height={560}
      style={{ background: 'transparent', display: 'block', mixBlendMode: 'screen', pointerEvents: 'none' }}
    />
  )
})
