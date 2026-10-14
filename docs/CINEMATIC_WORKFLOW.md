# CineForge — Workflow Cinematográfico Profissional para Comerciais

> Regras, técnicas e skills para geração de vídeos com qualidade Hollywood,
> continuidade absoluta e profissionalismo máximo.

---

## PARTE 1 — FUNDAMENTOS DA LINGUAGEM CINEMATOGRÁFICA

### 1.1 A Gramática dos Planos

| Código | Nome          | Enquadramento                          | Uso em Comerciais              |
|--------|---------------|----------------------------------------|-------------------------------|
| ELS    | Extreme Long Shot | Paisagem toda, personagem mínimo   | Estabelecimento de universo    |
| LS     | Long Shot      | Personagem inteiro + ambiente         | Ação física completa           |
| MLS    | Medium Long    | Joelho para cima                      | Movimento com contexto         |
| MS     | Medium Shot    | Cintura para cima                     | Diálogo, produto + pessoa      |
| MCU    | Medium Close-Up | Peito para cima                      | Emoção + produto visível       |
| CU     | Close-Up       | Rosto/produto                         | **O plano mais vendedor**      |
| ECU    | Extreme Close-Up | Olho, detalhe do produto            | Textura, impacto emocional     |
| OTS    | Over-The-Shoulder | Por cima do ombro                  | Conversa, apresentação         |
| POV    | Point of View  | Câmera = olho do personagem           | Imersão, produto em uso        |
| INS    | Insert Shot    | Detalhe isolado                       | Logo, call-to-action, preço    |

**Regra de ouro para comerciais**: Abrir com ELS ou LS para estabelecer → MS/MCU para contar → CU/ECU para o clímax emocional ou produto → Insert para CTA.

---

### 1.2 Movimentos de Câmera

```
ESTÁTICOS:
  - STATIC: câmera fixa no tripé → estabilidade, autoridade, luxo
  - DUTCH ANGLE: câmera inclinada ±15-30° → tensão, disrupção, energia

HORIZONTAIS:
  - PAN: rotação horizontal → seguir ação, revelar ambiente
  - DOLLY IN/OUT: câmera se move fisicamente → intimidade/revelação
  - TRUCK (LATERAL DOLLY): acompanha movimento paralelo → sensação de velocidade

VERTICAIS:
  - TILT UP/DOWN: revela grandiosidade ou queda
  - CRANE/JIB: move verticalmente + translada → deus-ex-machina visual
  - PEDESTAL: sobe/desce verticalmente sem inclinar

FLUIDOS:
  - STEADICAM: câmera na veste → fluidez seguindo personagem
  - HANDHELD: tremido intencional → urgência, realismo, energia
  - DRONE/AERIAL: perspectiva aérea → escala épica

ÓPTICOS (sem mover a câmera):
  - ZOOM IN/OUT: comprime/expande espaço visual
  - RACK FOCUS (PULL FOCUS): foco passa de um plano para outro → revela, conecta
  - PUSH IN (zoom lento): intensidade crescente, decisão iminente
```

**Técnica Hitchcock (Vertigo Effect / Dolly Zoom)**:  
Dolly para trás + zoom para frente simultaneamente = fundo estável + personagem isolado.  
Uso: revelação de produto, momento de impacto.

---

### 1.3 A Regra dos 180° (Eixo de Ação)

```
PERSONAGEM A ←————————————→ PERSONAGEM B
              |    EIXO    |
              |  INVISÍVEL |
         [CÂMERA SEMPRE
          DESTE LADO]
```

- **NUNCA cruzar o eixo** sem um shot neutro (câmera NO eixo) ou motivação de movimento
- Crossing the line = personagens parecem trocar de lado = desorientação do espectador
- Em comerciais com produto: câmera sempre do mesmo lado do produto durante sequência

**Regra dos 30°**: Mude o ângulo de câmera pelo menos 30° entre cortes do MESMO plano ou faça jump cut intencional.

---

### 1.4 Matches e Continuidade

```python
# TIPOS DE CORTE POR CONTINUIDADE:

MATCH CUT:       # Forma/movimento idêntico → duas cenas conectadas
                 # Exemplo: engrenagem girando → planeta girando (2001: A Space Odyssey)

EYELINE MATCH:   # Personagem olha para X → corte → X em POV
                 # ESSENCIAL: personagem olha para produto → produto aparece

GRAPHIC MATCH:   # Composição visual similar une dois planos
                 # Círculo azul → logo circular → orbe do produto

ACTION MATCH:    # Movimento idêntico em dois contextos diferentes
                 # Mão estendendo-se → recebendo produto

J-CUT:          # Áudio do próximo plano começa ANTES do corte visual
                # Voz over começa antes da cena aparecer → profissional

L-CUT:          # Áudio continua ALÉM do corte visual
                # Música/voz se estende para próxima cena → fluidez
```

---

## PARTE 2 — ILUMINAÇÃO CINEMATOGRÁFICA

### 2.1 Three-Point Lighting (Base Profissional)

```
        [KEY LIGHT]
           /
          / 45° acima, 45° lateral
         /
     [SUJEITO]
        |
       [FILL LIGHT]        [BACK/HAIR LIGHT]
       45° oposto           atrás, acima
       50% da intensidade   separa sujeito do fundo
```

**Para o estilo CineForge (Predador + Sci-Fi Verde)**:
- Key: luz verde néon forte lateral (45°) — simula tela holográfica
- Fill: luz ambiente escura (quase nula) — realça o preto absoluto
- Back: contraluz verde suave — borda cromada na armadura
- Practical: leds verdes embutidos na armadura — motivam a iluminação

### 2.2 Estilos de Iluminação por Objetivo

| Estilo             | Setup                          | Mood                          | Uso                      |
|--------------------|--------------------------------|-------------------------------|--------------------------|
| Rembrandt          | Key alto-lateral, sombra triangular | Drama, profundidade    | Retratos impactantes     |
| Hard Light         | Fonte pequena e direta         | Duro, sci-fi, industrial      | **Estilo CineForge**     |
| Soft Light         | Fonte grande/difusa            | Suave, emocional, natural     | Beleza, lifestyle        |
| Motivated Light    | Imita fonte real visível       | Realismo aumentado            | Telas, janelas, fogos    |
| Chiaroscuro        | Alto contraste luz/sombra      | Noir, thriller, luxury        | Premium, misterioso      |
| Practical Only     | Apenas luzes do ambiente       | Ultra-realismo                | Documental, urgência     |

### 2.3 Temperatura de Cor (Kelvin)

```
2000K  → Chama, vela — quente íntimo
3200K  → Tungstênio — cinema clássico
5600K  → Luz do dia — natural neutro
6500K  → Overcast — frio, clínico
8000K+ → Luz azul — sci-fi, noturno
∞ VERDE → Néon LED — CineForge Predador
```

---

## PARTE 3 — COLOR GRADING PROFISSIONAL

### 3.1 Pipeline de Cor

```
RAW/LOG FOOTAGE
      ↓
INPUT TRANSFORM (LUT técnico: ARRI LogC → Linear)
      ↓
CREATIVE GRADE (Look LUT — estilo visual)
      ↓
OUTPUT TRANSFORM (Rec.709 para digital / P3 para cinema)
      ↓
EXPORT
```

### 3.2 Looks Clássicos de Comerciais

| Look              | Características                              | Marcas que usam       |
|-------------------|----------------------------------------------|-----------------------|
| Orange & Teal     | Pele laranja, sombras azul-verde             | Blockbusters, games   |
| Bleach Bypass     | Baixa saturação, contraste alto              | Nike, Adidas thriller |
| Day for Night     | Azulado, subexposto                          | Dark, misterioso      |
| Cross-Process     | Cores erradas propositalmente                | Arte, vanguarda       |
| Desaturated       | Quase P&B, uma cor dominante                 | Luxo, minimalismo     |
| **Green Neon**    | **Preto puro + verde néon alto**             | **CineForge**         |

### 3.3 Parâmetros DaVinci Resolve para Look Sci-Fi Verde

```
Lift (Sombras):   R:-0.05  G:+0.02  B:+0.02  → sombras com toque verde-frio
Gamma (Médios):   R:-0.03  G:+0.05  B:-0.02  → médios esverdeados
Gain (Altas):     R:-0.08  G:+0.10  B:+0.02  → altas com verde dominante
Saturation:       1.3 → verde se destaca
Contrast:         1.4 → preto puro nas sombras
Pivot:            0.38 → sombras ocupam mais espaço tonal
Hue vs Sat (Verde): +40% → verde explode
```

---

## PARTE 4 — STORYBOARD E PRÉ-PRODUÇÃO PROFISSIONAL

### 4.1 Estrutura de Brief Cinematográfico

```markdown
## BRIEF DO COMERCIAL

### 1. SINGLE MINDED PROPOSITION (SMP)
Uma única frase que resume o que o espectador deve sentir/lembrar.
Ex: "CineForge transforma ideias em cinema de alta tecnologia."

### 2. PÚBLICO-ALVO
- Primário: [quem compra]
- Secundário: [quem influencia]
- Insight: [verdade humana que conecta produto ao público]

### 3. TOM E LINGUAGEM
- Emocional / Racional / Aspiracional
- Palavras-chave: [3-5 adjetivos]
- Anti-palavras: [o que NÃO somos]

### 4. ENTREGÁVEIS
- Formato: [16:9 / 9:16 / 1:1]
- Duração: [15s / 30s / 60s]
- Plataforma: [TV / Digital / Social]

### 5. REFERÊNCIAS VISUAIS
- [URL ou descrição de referências]
```

### 4.2 Shot List Profissional

```
| # | INT/EXT | LOCAL       | PLANO | ÂNGULO  | MOVIMENTO   | DESCRIÇÃO          | DURAÇÃO |
|---|---------|-------------|-------|---------|-------------|---------------------|---------|
| 1 | INT     | COCKPIT     | ELS   | HIGH    | DOLLY IN    | Reveal do cockpit   | 3s      |
| 2 | INT     | COCKPIT     | MCU   | EYE LVL | STATIC      | Predador olha câmera| 2s      |
| 3 | INT     | TELA HOLO   | ECU   | LOW     | RACK FOCUS  | Dados holográficos  | 1.5s    |
| 4 | INT     | COCKPIT     | CU    | HIGH    | PUSH IN     | Olhos verdes focus  | 2s      |
```

### 4.3 Tratamento (Treatment) — Documento de Diretores Hollywood

```markdown
## TREATMENT: "[Nome do Comercial]"
### Diretor: [Nome] | Agência: [Nome] | Cliente: [Marca]

### CONCEITO CENTRAL
[Parágrafo poético de 3-5 linhas descrevendo a EMOÇÃO central]

### REFERÊNCIAS VISUAIS PRINCIPAIS
- Cinematografia: [ex: Roger Deakins em Blade Runner 2049]
- Paleta de cor: [hex ou referência]
- Movimento de câmera: [referência de filme]

### ABERTURA (0-5 segundos)
[Descrição cinematográfica detalhada]

### DESENVOLVIMENTO (5-25 segundos)
[Beat by beat]

### CLÍMAX E PRODUTO (25-28 segundos)
[O momento de maior impacto]

### FECHAMENTO/CTA (28-30 segundos)
[Logo + tagline + call to action]

### CASTING
[Tipo de ator/personagem]

### LOCAÇÃO
[Descrição do ambiente]

### MÚSICA
[Gênero, BPM, referência de artista]
```

---

## PARTE 5 — TÉCNICAS DE GRANDES DIRETORES

### 5.1 Ridley Scott (Alien, Blade Runner, comerciais Apple)
- **Layered environments**: sempre múltiplas camadas de detalhe no fundo
- **Atmospheric haze**: névoa, vapor, fumaça para profundidade
- **Practical lights**: luzes reais no set iluminam a cena (não só key lights)
- **Contra-luz dramático**: personagem em silhueta contra luz intensa
- **Regra**: ambiente conta a história tanto quanto o personagem

### 5.2 David Fincher (comerciais Nike, Pepsi)
- **Perfeccionismo de movimento**: cada dolly move exato, repetido 50+ takes
- **Flat lighting + grade forte**: luz quase sem sombra no set, contraste na pós
- **Unsettling symmetry**: simetria perturbadora → inquietação elegante
- **Slow burn reveal**: câmera aproxima-se lentamente antes do corte
- **Regra**: cada frame deve funcionar como fotografia isolada

### 5.3 Spike Jonze (Levi's, IKEA, Adidas)
- **Unexpected POV**: câmera em lugares impossíveis ou inusitados
- **Long takes com ação coreografada**: plano-sequência de 30s+
- **Magic realism**: elemento fantástico tratado como normal
- **Regra**: a câmera tem personalidade própria, não é observadora neutra

### 5.4 Michel Gondry (Renault, Smirnoff)
- **In-camera effects**: truques práticos sem CGI → mais orgânico
- **Toylike cinematography**: mundo "feito à mão" deliberadamente
- **Music-driven editing**: cada corte sincronizado com batida
- **Regra**: a imperfeição técnica intencional É a técnica

### 5.5 Emmanuel Lubezki "Chivo" (Apple "1984"-era)
- **Natural light supremacy**: iluminação natural ou natural-motivated
- **Ultra-wide lenses + shallow focus**: 14-21mm a f/1.4 → distorção épica
- **Long takes de steadicam**: câmera nunca para, sempre flui

---

## PARTE 6 — EDITING E RITMO

### 6.1 Duração de Planos por Tipo de Comercial

```
LUXO / HIGH-END:     Planos longos (3-8s), poucos cortes, respiração lenta
ESPORTE / ENERGIA:   Planos curtos (0.5-2s), cortes rápidos, ritmo de música
TECNOLOGIA / SCI-FI: Mix: planos médios + close-ups técnicos, cut on beat
EMOCIONAL:           Varia: longo → corte brusco → longo → impacto
```

**Fórmula para 30 segundos**:
```
0-3s    → HOOK (gancho) — plano impactante, sem contexto ainda
3-8s    → MUNDO (contexto) — onde/quem/o quê
8-22s   → CONFLITO + BENEFÍCIO — problema → solução → produto
22-27s  → CLÍMAX EMOCIONAL — o momento de "ah-ha"
27-30s  → CTA + LOGO — simples, limpo
```

### 6.2 Regras de Editing

1. **Corte em movimento**: sempre cortar durante movimento (não quando parado)
2. **Corte no batimento**: sincronize cortes com kick/snare da música
3. **Rule of three**: estabelece → detalhe → reação = 3-shot combo
4. **Eye trace**: onde o espectador está olhando deve continuar no próximo plano
5. **Sound before cut**: o áudio do próximo plano começa 2-4 frames antes (J-cut)
6. **Breathing room**: após cortes rápidos, plano lento para o espectador "respirar"

---

## PARTE 7 — SOM E MÚSICA

### 7.1 Layers de Som Profissional

```
LAYER 1 — MÚSICA (score/track):
  BPM: 90-130 para ação / 60-80 para emocional
  Estilo: orquestral épico / eletrônico / híbrido

LAYER 2 — SFX (sound effects):
  Ambientes: hum de cockpit, zumbido de telas, vapor
  Ações: servos mecânicos, hologramas ativando, pisadas metálicas
  Impactos: hits sincronizados com cortes rápidos (stingers)

LAYER 3 — VOICE OVER:
  Técnica: voz grave, pausada, com reverb sutil
  Respiração: pausas de 0.5s entre frases-chave
  Posicionamento: começa na frase, não antes da imagem

LAYER 4 — ROOM TONE:
  Sempre presente (silence ≠ ausência de som)
  Para sci-fi: hum eletrônico de baixa frequência (40-80Hz)
```

### 7.2 Técnica de Sincronização Música/Imagem

```
DOWNBEAT:    Corte principal (cena começa/termina)
UPBEAT:      Movimento começa (dolly, ação)
SNARE:       Cut abrupto / impacto visual
BASS DROP:   Reveal do produto / momento épico
RISER:       Sequência de close-ups crescendo
FADEOUT:     CTA screen / logo
```

---

## PARTE 8 — WORKFLOW DE GERAÇÃO AI CINEMATOGRÁFICA

### 8.1 Prompt Engineering para Qualidade Cinematográfica

**ESTRUTURA PADRÃO DO PROMPT**:
```
[SUJEITO] + [AÇÃO] + [AMBIENTE] + [ILUMINAÇÃO] + [CÂMERA] + [ESTILO]
```

**Exemplo CineForge**:
```
"alien predator warrior in black chrome armor, 
standing in dark sci-fi command center, 
surrounded by green holographic displays and atmospheric steam fog, 
dramatic green neon rim lighting from left, fill shadow on right, 
medium close-up shot at eye level, slight low angle for authority, 
cinematic 2.39:1 anamorphic, 8K ultra-detailed, photorealistic,
hyper-realistic 3D render, no watermark, no text overlay"
```

**Palavras-chave de qualidade cinematográfica**:
```
FOTORREALISMO:
  - "photorealistic", "hyperrealistic", "8K", "ultra-detailed"
  - "physically based rendering", "ray tracing", "subsurface scattering"

ESTILO CINEMATOGRÁFICO:
  - "anamorphic lens", "2.39:1 aspect ratio", "film grain"
  - "cinematic lighting", "dramatic shadows", "depth of field"
  - "bokeh background", "lens flare", "chromatic aberration (subtle)"

QUALIDADE DE PRODUÇÃO:
  - "professional commercial", "Hollywood production quality"
  - "award-winning photography", "Oscars winning cinematography"
  - "shot on ARRI Alexa", "Panavision lens"

NEGATIVOS (sempre incluir):
  - "no watermark, no text overlay, no signature"
  - "no cartoon, no anime, no illustration"
  - "no distortion, no artifacts, no noise"
```

### 8.2 Continuidade entre Planos (Multi-Shot Consistency)

**PARA MANTER CONSISTÊNCIA VISUAL**:

```python
# Elementos que DEVEM ser idênticos em todos os prompts de uma sequência:
FIXED_ELEMENTS = {
    "personagem": "alien predator, black chrome metallic armor, green glowing eyes",
    "ambiente": "dark sci-fi command center, pure black background",
    "iluminação": "green neon dominant, hard left rim light",
    "paleta": "black and neon green only, no warm colors",
    "qualidade": "hyperrealistic, 8K, cinematic, no watermark",
}

# Apenas ISSO muda entre planos:
VARIABLE_PER_SHOT = {
    "enquadramento": "extreme wide / medium / close-up / extreme close-up",
    "ângulo": "high angle / eye level / low angle / dutch",
    "ação": "standing / activating hologram / turning head / eyes glowing",
    "destaque": "full body / hands / face / eyes / armor detail",
}
```

### 8.3 Shot-by-Shot Bible (Template para Geração)

```python
CINEFORGE_SHOT_BIBLE = {
    "shot_01_master": {
        "type": "Extreme Long Shot",
        "angle": "High angle, 60° down",
        "movement": "Slow dolly in over 5 seconds",
        "prompt": "extreme wide establishing shot, alien predator in center "
                  "of vast dark command center, dozens of green holographic screens "
                  "surrounding, atmospheric steam rising, pure black background, "
                  "dramatic top-down green neon lighting, cinematic 2.39:1, 8K",
        "duration_seconds": 4,
        "audio": "deep electronic hum, steam sfx",
    },
    "shot_02_medium": {
        "type": "Medium Shot",
        "angle": "Eye level, slight low",
        "movement": "Static",
        "prompt": "medium shot alien predator standing, black chrome armor "
                  "with green LED joints glowing, green holographic data streams "
                  "visible at edges of frame, atmospheric fog at feet, "
                  "dramatic green rim lighting, neutral dark background, 8K cinematic",
        "duration_seconds": 3,
        "audio": "servo mechanics sfx, music enters",
    },
    "shot_03_closeup": {
        "type": "Close-Up",
        "angle": "Eye level",
        "movement": "Slow push in",
        "prompt": "close-up face alien predator, intense green glowing eyes, "
                  "black chrome helmet reflecting green holographic screens, "
                  "atmospheric steam wisps, hard green neon sidelight, "
                  "deep shadow opposite side, 8K photorealistic cinematic",
        "duration_seconds": 2.5,
        "audio": "music builds, riser",
    },
    "shot_04_extreme_closeup": {
        "type": "Extreme Close-Up",
        "angle": "Eye level",
        "movement": "Rack focus from iris to background",
        "prompt": "extreme close-up alien predator eye, pupil glowing intense green, "
                  "reflections of holographic command center visible in iris, "
                  "microscopic armor texture visible, hard specular green rim light, "
                  "8K macro photorealistic cinematic, shallow depth of field",
        "duration_seconds": 1.5,
        "audio": "bass drop, music peak",
    },
}
```

---

## PARTE 9 — SKILLS E REGRAS DO SISTEMA CINEFORGE

### 9.1 Skill: PRÉ-PRODUÇÃO

```
REGRA 1 — SINGLE MINDED PROPOSITION:
  Antes de qualquer geração, definir UMA única emoção/mensagem.
  Não proceder sem SMP clara.

REGRA 2 — VISUAL BIBLE:
  Criar documento com: paleta exata, personagem descrito em 3 linhas,
  ambiente descrito em 3 linhas, iluminação descrita em 2 linhas.
  Este documento guia TODOS os prompts.

REGRA 3 — SHOT LIST ANTES DE GERAR:
  Planejar TODOS os planos antes de gerar o primeiro frame.
  Shot list define: quantidade, sequência, duração de cada plano.

REGRA 4 — REFERÊNCIAS VISUAIS:
  Citar pelo menos 1 filme/comercial de referência para cinematografia.
  Citar pelo menos 1 referência de paleta de cor.
```

### 9.2 Skill: GERAÇÃO DE IMAGENS

```
REGRA 5 — PROMPT STRUCTURE:
  Todo prompt DEVE conter: sujeito + ação + ambiente + iluminação + câmera + qualidade.
  Prompt sem câmera/iluminação = resultado amador. SEMPRE incluir.

REGRA 6 — ELEMENTOS FIXOS:
  Copiar EXATAMENTE os fixed elements do Visual Bible em cada prompt.
  NUNCA reescrever com sinônimos — modelo AI é sensível a variações de texto.

REGRA 7 — NEGATIVOS:
  Sempre incluir: "no watermark, no text, no signature, no artifacts".
  Para hiper-realismo sempre adicionar: "no illustration, no cartoon style".

REGRA 8 — RESOLUÇÃO:
  Sempre especificar 8K ou "ultra high resolution" para qualidade máxima.
  Adicionar "hyperrealistic" + "physically based rendering" para fotorrealismo.
```

### 9.3 Skill: CONTINUIDADE

```
REGRA 9 — VISUAL CONSISTENCY CHECK:
  Antes de aprovar um plano, verificar:
  [ ] Personagem idêntico ao plano anterior?
  [ ] Paleta de cor consistente?
  [ ] Direção de iluminação consistente?
  [ ] Ambiente reconhecível como o mesmo?

REGRA 10 — TRANSIÇÃO DE PLANOS:
  Wide → Medium → Close-Up = ordem CORRETA (estabelece contexto primeiro)
  Close-Up → Wide sem medium = jump cut (use só intencionalmente)
  Dois close-ups seguidos do mesmo ângulo = erro (mudar ângulo 30°+)

REGRA 11 — 180° RULE:
  Personagem/produto sempre do mesmo lado da tela durante uma sequência.
  Para mudar: inserir plano neutro (câmera no eixo) ou cut away.

REGRA 12 — COLOR CONTINUITY:
  Não misturar looks quentes e frios sem intenção.
  Para CineForge: verde néon SEMPRE, zero amarelo/laranja/vermelho.
```

### 9.4 Skill: EDIÇÃO E RITMO

```
REGRA 13 — CORTE NO MOVIMENTO:
  Nunca cortar quando ação está parada (fica "jumpado").
  Sempre cortar quando movimento está acontecendo.

REGRA 14 — SINCRONIZAÇÃO MUSICAL:
  Mapear BPM da música antes de editar.
  Cortes principais = downbeats.
  Impactos = snare/kick.

REGRA 15 — PACING BY EMOTION:
  Emoção sobe = planos ficam mais curtos.
  Emoção cai = planos ficam mais longos.
  Variação de duração = tensão dramática.

REGRA 16 — J-CUT/L-CUT:
  Preferir J-cuts e L-cuts a cortes secos.
  Áudio do próximo plano entrando 2-4 frames antes = fluidez profissional.
```

### 9.5 Skill: QUALIDADE FINAL

```
REGRA 17 — FRAME POR FRAME REVIEW:
  Assistir o corte final sem áudio primeiro.
  Cada frame deve funcionar como fotografia isolada.

REGRA 18 — COLOR GRADE FINAL:
  Aplicar LUT criativo DEPOIS de equalizar exposição de todos os planos.
  Consistência de cor entre planos é prioridade máxima.

REGRA 19 — SOUND DESIGN:
  Mínimo 3 layers de som: música + SFX + room tone.
  Ausência de som = escolha criativa, não descuido.

REGRA 20 — EXPORT SPECS:
  Digital: H.264/H.265, 1920x1080 mínimo, 8Mbps+
  Web/Social: H.264, bitrate adaptivo
  Cinema/TV: ProRes 422 HQ, 4K mínimo
```

---

## PARTE 10 — REFERÊNCIAS OBRIGATÓRIAS

### Filmes para Estudar Cinematografia de Comerciais
1. **Blade Runner 2049** (Deakins) — iluminação néon em ambientes escuros
2. **Mad Max: Fury Road** — cortes em ação, energia máxima
3. **The Revenant** (Lubezki) — uso de luz natural, longos takes
4. **Ex Machina** — sci-fi minimalista, tecnologia + emoção
5. **1984 Apple Commercial** (Ridley Scott) — 60s que mudou a publicidade

### Produtoras de Referência
- **RSA Films** (Ridley Scott Associates) — técnica + arte
- **MJZ** — performance-driven, direção de atores
- **Pulse Films** — music videos + comerciais energéticos
- **Anonymous Content** — Fincher, narrativa forte

### Ferramentas do Workflow
- **StudioBinder** — shot lists e storyboards profissionais
- **DaVinci Resolve** — color grading (gratuito, industry-standard)
- **Frame.io** — review e aprovação de cortes
- **Adobe Premiere** — edição com proxy workflow
- **ShotDeck** — banco de referências cinematográficas

---

## APÊNDICE — VISUAL BIBLE CINEFORGE

```python
CINEFORGE_VISUAL_BIBLE = """
PERSONAGEM:
  alien predator warrior, towering 7-8 feet tall,
  full-body black chrome metallic armor with green LED accent lights at all joints,
  helmet with glowing intense green eyes visible through dark visor,
  no visible skin, completely armored, battle-ready stance

AMBIENTE:
  dark sci-fi command center, pure absolute black background,
  multiple floating green holographic screens surrounding the character,
  atmospheric steam and fog at ground level,
  no other characters, isolated and powerful

ILUMINAÇÃO:
  dominant hard green neon sidelight from left (simulates holographic screen),
  green LED rim light from behind (separates from black background),
  zero fill light — deep shadows on right side,
  no warm colors whatsoever

PALETA:
  100% black and neon green only,
  hex: background #000000, primary neon #00FF41, secondary #00CC33
  forbidden: any red, orange, yellow, warm tones

QUALIDADE:
  hyperrealistic 8K photorealistic render,
  anamorphic cinematic 2.39:1,
  no watermark, no text, no signature
"""
```

---

*Versão 1.0 — CineForge Cinematographic Workflow*  
*Baseado em técnicas de Hollywood, produtoras internacionais e faculdades de cinema*
