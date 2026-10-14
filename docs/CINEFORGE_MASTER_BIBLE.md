# CINEFORGE MASTER BIBLE
### Referência Definitiva para Produção Cinematográfica AI de Nível Hollywood
**Versão 1.0 — Outubro 2026**

---

## ÍNDICE GERAL

1. Character Bible
2. Environment Bible
3. Costume & Wardrobe Bible
4. Master Prompt System
5. Audio & Sound Bible
6. VFX & Effects Bible
7. Color Bible
8. Ferramentas Ranqueadas
9. 50 Regras de Ouro

---

---

# PARTE 1 — CHARACTER BIBLE

## 1.1 — PRINCÍPIO FUNDAMENTAL

> **REGRA DE OURO ABSOLUTA:** CREATE ONCE. LOCK THE IDENTITY. REUSE THE REFERENCE. REPEAT THE CHARACTER DESCRIPTION. CHANGE ONLY WHAT THE STORY REQUIRES.

A consistência de personagem é o maior desafio técnico da produção cinematográfica AI. Sem um sistema rigoroso documentado, cada geração começa do zero e o personagem deriva. Este capítulo define o sistema que elimina esse problema.

---

## 1.2 — TEMPLATE DE PERSONAGEM (Preencher para cada personagem)

```
=== FICHA DE PERSONAGEM ===

NOME FICTÍCIO ÚNICO: [Nome inventado específico — ex: Kael Dawnforge]
PAPEL NA NARRATIVA: [Protagonista / Antagonista / Secundário]

--- IDENTIDADE VISUAL IMUTÁVEL (NUNCA mude entre planos) ---

ESTRUTURA ÓSSEA:
- Formato do rosto: [oval / quadrado / coração / diamante / oblongo]
- Espaçamento dos olhos: [próximos / médios / afastados]
- Largura da mandíbula: [estreita / média / larga]
- Proeminência das maçãs do rosto: [baixa / média / alta]
- Formato do nariz: [romano / arrebitado / largo / afilado]

OLHOS:
- Cor exata: [ex: emerald green / amber / steel blue / dark brown]
- Formato: [amendoado / redondo / puxado / com canto externo caído]
- Sobrancelhas: [espessas / finas / arqueadas / retas / arqueamento na ponta]

TRAÇOS DISTINTIVOS (âncoras de identidade):
- [Cicatriz acima do olho esquerdo, 2cm, diagonal]
- [Marca de nascença triangular no pescoço direito]
- [Sardas nas bochechas]
- [Fossinha no queixo]

TOM DE PELE: [ex: medium olive — HEX #C68642]

--- CABELO (muda com o tempo, mas documentar estado base) ---
- Cor base: [ex: dark brown with copper highlights]
- Comprimento: [ex: shoulder-length]
- Estilo: [ex: slightly messy, natural waves]
- Textura: [ex: thick, slightly coarse]

--- PROPORÇÕES CORPORAIS ---
- Altura relativa: [ex: 6ft2 — mostre ao lado de porta padrão]
- Build: [ex: muscular athletic, broad shoulders 1.5x hip width]
- Postura característica: [ex: upright, slight forward lean when focused]
- Como caminha: [ex: confident measured stride, light on feet]

--- IDENTIDADE SEMÂNTICA (prompt anchor — copie idêntico em TODOS os prompts) ---

ANCHOR PHRASE:
"[NOME], [etnia/fenótipo], [idade], [build], [cabelo exato], 
[olhos cor + formato], [traço distintivo 1], [traço distintivo 2], 
[postura característica]"

EXEMPLO COMPLETO:
"Kael Dawnforge, bronze-skinned warrior, mid-30s, 6ft2 muscular 
athletic build, shoulder-length dark brown hair with copper highlights, 
amber eyes with vertical scar across left eyebrow, confident upright 
stance, slight forward lean when focused"

--- REFERÊNCIAS VISUAIS ---
- Imagem âncora principal: [URL ou caminho do arquivo]
- Character sheet (4 ângulos): [URL ou caminho]
- Expression sheet (6 expressões): [URL ou caminho]
- Imagem de corpo inteiro: [URL ou caminho]

SEED FIXO (plataforma):
- Midjourney seed: [número]
- Stable Diffusion seed: [número]
- LoRA path: [caminho do arquivo .safetensors]

=== FIM DA FICHA ===
```

---

## 1.3 — SISTEMA DE REFERENCE SHEETS (O que gerar ANTES de qualquer cena)

### TURNAROUND SHEET (Obrigatório — 4 a 6 ângulos)

**Prompt Midjourney:**
```
character turnaround sheet of [ANCHOR PHRASE], white background, 
front view, 3/4 left view, pure side profile view, back view, 
3/4 rear view, same consistent character all views, animation 
production style, professional character design, on model, 
no shadows competing, clean spacing --cref [URL_base] --cw 100 
--ar 16:9 --v 7
```

**Regra de geração:**
- Iluminação: neutra, difusa, sem drama
- Fundo: branco ou cinza neutro
- Expressão: neutra (sério mas relaxado)
- Roupas: traje assinatura completo
- Pose: anatomicamente padrão, sem ação

### EXPRESSION SHEET (Obrigatório — 6 expressões mínimas)

```
expression sheet of [ANCHOR PHRASE], 6 expressions: neutral, 
happy, angry, sad, surprised, determined, same character 
consistent in all expressions, white background, professional 
character design reference sheet, consistent lighting across 
all panels --cref [URL_turnaround] --cw 100 --ar 16:9
```

### SCALE REFERENCE SHEET (Obrigatório)

Gere o personagem ao lado de: porta padrão, cadeira, carro, segundo personagem da história. Isso trava a proporção de escala para planos de conjunto.

---

## 1.4 — HIERARQUIA DE MÉTODOS DE CONSISTÊNCIA

### MÉTODO 1 — Image-to-Video (Padrão mínimo para todo projeto)

- Gere sempre a cena como imagem estática primeiro
- Use essa imagem como primeiro frame no gerador de vídeo
- Nunca gere cenas com personagem via text-to-video puro
- Funciona em: Kling AI, Runway Gen-4, Luma Ray 3, Sora

### MÉTODO 2 — Character Reference (Ferramentas nativas)

| Ferramenta | Parâmetro | Como usar |
|---|---|---|
| Midjourney V7 | --cref [URL] --cw 100 | URL da turnaround sheet |
| Kling AI 3.0 | Elements / Character ID | Upload 3-5 ângulos do personagem |
| Runway Gen-4.5 | Image References | Upload turnaround + perfil |
| Seedance 2.5 | Omni Reference | @Image1 no prompt |
| Google Veo 3.1 | Ingredients to Video | Múltiplas imagens de referência |
| Sora 2 | Character Objects | Clip de 3+ segundos como objeto |

**Regra crítica de referência:**
- Use 2 a 3 imagens de referência, nunca 6 ou mais
- Imagens devem ter fundo limpo, iluminação neutra
- Nunca use imagem com expressão extrema como referência base
- Frontal + Perfil = combinação ideal para maioria das plataformas

### MÉTODO 3 — LoRA Customizado (Para projetos com 20+ cenas)

**Quando treinar:** 20+ clips do mesmo personagem na produção.

**Dataset de treino:**
- Quantidade mínima: 15-30 imagens
- Quantidade ideal: 50+ imagens para Very High consistency
- Variar: 5 ângulos x 3 iluminações x 4-5 expressões x 3 distâncias de câmera
- Manter idênticos: todas as características físicas e de roupa
- Tag universal em todas as imagens: `solo character, simple background, full body, [NOME ÚNICO] character`

**Ferramentas para treino:**
- Kohya SS (mais configurável)
- ai-toolkit (mais simples)
- Wan 2.2 (recomendado para personagem em vídeo)

**Parâmetros de aplicação:** peso 0.7 a 0.9

**Tempo:** 30 a 60 minutos em GPU moderna. Investimento que se paga após 5 cenas.

### MÉTODO 4 — Face Swap em Pós-Produção (Controle máximo)

1. Gere a cena com personagem genérico com corpo/iluminação corretos
2. Use FaceFusion ou Reactor para mapear o rosto da turnaround sheet
3. Resultado: composição física perfeita + identidade facial consistente

Custo: duas gerações por cena, mas elimina hallucinations e economiza créditos de regeNeração.

---

## 1.5 — TÉCNICAS DE ENVELHECIMENTO E REJUVENESCIMENTO

### Princípio Fundamental do Aging Cinematográfico

O envelhecimento correto preserva a identidade enquanto muda apenas os marcadores temporais. O erro mais comum em AI é mudar a estrutura óssea — isso cria um personagem diferente, não o mesmo personagem mais velho.

**Elementos IMUTÁVEIS em qualquer idade:**
- Cor dos olhos e formato básico
- Estrutura óssea facial (formato do crânio, espaçamento dos olhos)
- Marcas distintivas (cicatrizes, manchas de nascença)
- Formato básico do nariz e orelhas
- Proporção geral do rosto

**Elementos que MUDAM gradualmente:**
- Textura da pele e rugas
- Cor e espessura do cabelo
- Peso corporal e tônus muscular
- Postura (mais curvada com a idade)
- Expressão habitual de cansaço ou sabedoria

### Sistema de 5 Estágios (Staged Progression)

Nunca salte de jovem para idoso diretamente. Use intermediários:

| Estágio | Faixa | Descritores-chave |
|---|---|---|
| 1 | 18-25 | smooth taut skin, bright eyes, no lines, full face volume, youthful energy |
| 2 | 26-40 | subtle expression lines, defined character, slight nasolabial folds, confident maturity |
| 3 | 41-55 | pronounced expression lines, gray temples possible, reduced elasticity, established authority |
| 4 | 56-70 | deep character lines, full silver/gray hair, sagging beginning, distinguished presence |
| 5 | 71+ | deep structural changes, thin white hair, pronounced jowls, wise calm expression |

### Templates de Prompt por Estágio

**ESTÁGIO 1 (18-25):**
```
[ANCHOR PHRASE], age [X], young adult, smooth taut skin, 
bright eyes, no wrinkles, full face volume, [cor original do cabelo], 
youthful energy, inexperienced eyes, same facial bone structure, 
same [traços únicos], photorealistic
```

**ESTÁGIO 2 (26-40):**
```
[ANCHOR PHRASE], age [X], adult, subtle laugh lines beginning, 
defined facial character, [cor do cabelo] with possible first gray 
strands, confident expression, same distinctive [traços], 
natural aging progression, photorealistic
```

**ESTÁGIO 3 (41-55):**
```
[ANCHOR PHRASE], middle-aged, age [X], pronounced expression lines, 
silver temples, deeper nasolabial folds, reduced skin elasticity, 
[cabelo com mais grisalho], mature authority, weathered but strong, 
same bone structure, same [traços únicos], photorealistic
```

**ESTÁGIO 4 (56-70):**
```
[ANCHOR PHRASE], elderly, age [X], deep character lines, 
full silver-gray hair, skin sagging at jaw, age spots on temples, 
crow's feet, forehead lines, dignified bearing, wisdom in eyes, 
same [cor dos olhos], same distinctive [traços], photorealistic
```

**ESTÁGIO 5 (71+):**
```
[ANCHOR PHRASE], aged, age [X], white hair, deep structural 
facial changes, pronounced jowls, thin parchment skin, deep 
grooves, slight stoop, serene wise expression, same [cor dos olhos], 
same [marcas únicas], photorealistic
```

### Envelhecimento por Estilo de Vida

Adicione ao prompt base conforme o histórico do personagem:

- **Trabalhador externo:** `sun-weathered skin, deep laugh lines, squint lines from sun exposure, tan complexion, strong weathered hands, robust physique maintained`
- **Estudioso/intelectual:** `pale scholarly skin, reading glasses, thoughtful brow furrows, bookish expression lines, thin frame`
- **Guerreiro/soldado:** `battle-hardened face, asymmetric battle scars, muscular aging build, alert warrior bearing, intense eyes, weathered from elements`
- **Líder/político:** `distinguished silver hair, confident jaw, authority lines, well-maintained appearance, deliberate controlled expression`

### Prompt Negativo para Aging (Incluir em TODAS as gerações de idade)

```
different eye color, different face shape, changed nose, altered bone 
structure, inconsistent features, cartoonish aging, flat wrinkles, 
unrealistic skin, plastic appearance, uncanny smoothness, 
different person, identity shift, surgery look, uniform wrinkles, 
artificial aging
```

---

## 1.6 — CHECKLIST DE CONSISTÊNCIA (Verificar antes de cada geração)

```
CHECKLIST DE CONSISTÊNCIA DE PERSONAGEM

PRÉ-GERAÇÃO:
[ ] Anchor phrase idêntica ao padrão documentado
[ ] Mesmas palavras, mesma ordem, mesma ortografia
[ ] Imagem de referência selecionada (turnaround ou perfil)
[ ] Seed documentado se usando SD/ComfyUI
[ ] LoRA path correto se aplicável
[ ] Aspect ratio idêntico ao restante da produção

IDENTIDADE VISUAL:
[ ] Cor dos olhos corresponde ao documento
[ ] Estrutura óssea não foi descrita de forma diferente
[ ] Traços distintivos estão no prompt
[ ] Cabelo: cor exata e estilo idênticos ao estágio de idade correto
[ ] Tom de pele: descrição idêntica (nunca varie entre 'bronze' e 'tan')

VESTUÁRIO:
[ ] Outfit correto para a cena (verificar Script Day)
[ ] Referência visual do vestuário incluída
[ ] Desgaste do figurino corresponde ao ponto da narrativa

PÓS-GERAÇÃO:
[ ] Face é reconhecível como o personagem?
[ ] Olhos: cor correta?
[ ] Cabelo: cor e estilo corretos?
[ ] Traços distintivos visíveis quando aplicável?
[ ] Proporções corporais coerentes com cenas anteriores?
[ ] Vestuário está correto para esta cena?
[ ] Iluminação e temperatura de cor compatíveis com cenas adjacentes?

SE ALGUM ITEM FALHOU:
-> Identifique UM elemento inconsistente
-> Ajuste apenas esse elemento no prompt
-> Nunca mude o prompt inteiro de uma vez
```

---

---

# PARTE 2 — ENVIRONMENT BIBLE

## 2.1 — PRINCÍPIO FUNDAMENTAL

> O mundo existe ANTES dos personagens. As regras visuais do mundo definem quem pode habitar aquele mundo. Personagens sem mundo definido flutuam sem contexto.

Assim como personagens derivam entre cenas, cenários também mudam se não forem ancorados. Este capítulo define o sistema para manter mundos coerentes.

---

## 2.2 — PERGUNTA-ÂNCORA DO MUNDO

Antes de gerar qualquer visual de ambiente, responda:

**"O que torna este mundo visualmente único, e qual lógica social ou física governa como ele parece?"**

Esta pergunta impede decoração genérica e força coerência funcional.

Exemplos:
- "Utopia corporativa corroída por baixo: fachadas impecáveis, bastidores em decomposição"
- "Pós-colapso com tecnologia patchwork: novo convivendo com ruína de forma improvisada"
- "Mundo orgânico-tecnológico: arquitetura que respira, estruturas que crescem"

---

## 2.3 — TEMPLATE DE CENÁRIO (Preencher para cada localização)

```
=== FICHA DE CENÁRIO ===

NOME DO LOCAL: [Ex: Estação Orbital Kepler-9]
FUNÇÃO NARRATIVA: [Para que esse lugar serve na história]
TIPO: [Interior / Exterior / Misto]
PERÍODO TEMPORAL: [Quando na timeline da história]

--- IDENTIDADE VISUAL IMUTÁVEL ---

PALETA DE CORES (códigos HEX obrigatórios):
- Cor dominante (60%): [HEX + descrição: ex: #1A1A2E deep navy void]
- Cor secundária (30%): [HEX + descrição]
- Cor de acento (10%): [HEX + descrição]
- Cor de neon/prático (quando presente): [HEX]

MATERIAIS PREDOMINANTES:
- Superfície principal: [ex: brushed anodized aluminum, grade 6061]
- Texturas secundárias: [ex: tempered glass panels, industrial rubber seals]
- Elemento de contraste: [ex: exposed oxidized copper piping]

ILUMINAÇÃO (Regras imutáveis deste cenário):
- Fonte principal: [ex: blue-white fluorescent overhead, slightly flickering]
- Temperatura de cor base: [ex: 4200K cool white]
- Direção dominante: [ex: top-down with left fill]
- Hora do dia canônica: [ex: perpetual night / always golden hour]
- Regra de sombra: [ex: hard shadows 70% coverage]
- Fontes práticas visíveis: [ex: wall-mounted emergency lights, holographic screens]

ARQUITETURA/ESTILO:
- Referência estética principal: [ex: brutalist Soviet + NASA Apollo era]
- Proporções espaciais: [ex: vast ceiling height, narrow corridors]
- Tecnologia característica: [ex: analog gauges alongside digital interfaces]
- Nível de desgaste: [ex: 15 years of use — visible but maintained]
- Modificações/improvisações: [ex: duct tape repairs, hand-written labels over screens]

ATMOSFERA:
- Tipo: [ex: Volumetric fog / Fine atmospheric haze / Clean air]
- Densidade: [ex: medium — obscures 30% of background detail]
- Elementos em suspensão: [ex: dust particles in light shafts]
- Som ambiente visual: [ex: steam vents every 8 seconds]

EVIDÊNCIAS DE HISTÓRIA (anti-render de propaganda):
- Desgaste 1: [ex: blast scoring on far wall from incident in Year 2]
- Desgaste 2: [ex: graffiti in access corridor, partially painted over]
- Modificação 1: [ex: extra lighting rig jury-rigged with exposed cabling]
- Objeto pessoal: [ex: photo taped to workstation, plant in window]

--- DESCRIÇÃO PADRÃO (para prompt — copiar identicamente em todas as cenas) ---

LOCATION ANCHOR PHRASE:
"[NOME DO LOCAL], [materiais], [iluminação base], [atmosfera], 
[elementos característicos], [nível de desgaste], [hora/estação canônica]"

EXEMPLO:
"Kepler-9 orbital station interior, brushed aluminum walls with 
tempered glass panels, cool blue-white fluorescent overhead with slight 
flicker, fine atmospheric haze with dust particles in light shafts, 
emergency lighting casting red secondary glow on right, 15 years of use 
showing — duct tape repairs and hand-written labels visible, perpetual 
station night through viewports"

--- REFERÊNCIAS VISUAIS ---
- Environment plate (vazio, sem personagens): [URL]
- Referência com personagem para escala: [URL]
- Referências de detalhes: [URL x3]

--- SHOTS OBRIGATÓRIOS (gerar para cada cenário) ---
[ ] Establishing wide shot (vazio, sem personagens)
[ ] Medium shot reference (com personagem para escala)
[ ] Close-up de elemento arquitetônico característico
[ ] Detalhe de desgaste/história

=== FIM DA FICHA DE CENÁRIO ===
```

---

## 2.4 — GRAMÁTICA VISUAL DO MUNDO CINEFORGE

Define as regras implícitas que permitem ao espectador "ler" o mundo sem explicação.

### Paleta por Classe Social / Hierarquia

| Nível | Cor | Material | Luz |
|---|---|---|---|
| Elite / Corporativo | #C8B8A2 creme e brancos frios | Mármore, vidro temperado, aço polido | Natural indireta, luz do dia controlada |
| Classe média / Trabalhadora | #4A5568 azuis-cinzas | Concreto, plástico ABS, alumínio | Fluorescente funcional |
| Subterrâneo / Marginal | #1A1A2E escuros com neon | Metal enferrujado, plástico improvisado | Neon, luz prática, fogo |
| Natureza / Orgânico | #2D5A27 verdes terrosos | Madeira, pedra, plantas vivas | Luz solar direta, luz de fogo |

### Regras de Ângulo por Emoção

| Emoção | Ângulo | Movimento |
|---|---|---|
| Poder / Dominância | Low angle (câmera abaixo, olhando para cima) | Dolly lento para frente |
| Vulnerabilidade | High angle (câmera acima, olhando para baixo) | Tilt lento para baixo |
| Mistério / Tensão | Dutch angle (inclinado 10-20°) | Handheld ligeiro |
| Isolamento / Solidão | Bird's eye / overhead | Estático ou pull back lento |
| Intimidade / Humanidade | Eye level, close | Push in lento |
| Épico / Grandiosidade | Extreme wide, eye level ou ligeiro low | Crane sweep ou drone |

### Iluminação como Narrativa (Regras do mundo)

| Situação | Iluminação | Significado |
|---|---|---|
| Neon exterior frio + interior quente | Contraste térmico | Tensão entre fachada pública e humanidade privada |
| God rays + névoa | Volumétrica dramática | Mistério, sagrado, transcendência |
| Luz prática piscando | Prática instável | Perigo, decadência, urgência |
| Golden hour difusa | Hora dourada | Esperança, memória, fim de ciclo |
| Luz azul fria, sem fontes práticas | Ambiental fria | Tecnologia sem calor humano, isolamento |
| Única fonte lateral dura | Chiaroscuro | Moral ambígua, segredo, dualidade |

---

## 2.5 — FRAMEWORK 5S PARA QUALQUER PROMPT DE CENÁRIO

Todo prompt de cena deve incluir os 5 elementos nesta ordem:

1. **Subject** — O que o sujeito/sistema é
2. **Sequence** — O movimento (câmera ou elemento)
3. **Setting** — O ambiente com 4 camadas de detalhe
4. **Shot** — Tipo de plano e ângulo
5. **Style** — Referência estética + paleta

**Exemplo estruturado completo:**
```
[Subject] Angular interceptor fighter craft with forward-swept 
titanium wings and exposed thruster arrays —

[Sequence] executes high-speed banking turn, engine glow leaves 
light trail, cockpit canopy reflects nebula colors, motion blur 
on wingtips —

[Setting] backdrop of dense nebula field: layer 1: distant star 
clusters, layer 2: gaseous purple nebula formations, layer 3: 
debris field from recent battle, layer 4: volumetric light shafts 
through nebula openings —

[Shot] camera tracks ship through turn maintaining cinematic 
focus, slight low angle to emphasize scale —

[Style] sleek military design with reflective metallic surfaces, 
Blade Runner meets Top Gun Maverick aesthetic, teal and orange 
complementary palette, anamorphic lens flare on engine core —

[Technical] cinematic 2.39:1, photorealistic, 8K
```

---

## 2.6 — PROMPTS COMPLETOS POR TIPO DE AMBIENTE

### Megacidade Cyberpunk / Noturna
```
Dense vertical megacity at perpetual night, layered transit systems 
visible at three altitude levels, neon signs in multiple languages 
cast overlapping colored reflections on rain-slicked cobblestone 
below, flying vehicles leave light trails between brutalist towers, 
steam rises from street-level industrial vents, warm amber interior 
lights behind rain-streaked windows contrast cold exterior neon blue 
and magenta, fine atmospheric haze reduces visibility at upper stories, 
camera tilts slowly upward from ground level revealing towering 
architecture, Blade Runner meets contemporary Tokyo aesthetic, 
deep purple-black with cyan and orange accents, anamorphic 2.39:1
```

### Base Lunar / Instalação Derelict
```
Derelict lunar research base interior, cracked transparent dome panels 
show harsh star field above, dead plants visible in overgrown 
hydroponics bays, emergency lighting flickers intermittently casting 
red glow across corridor, dust and small debris float in low gravity, 
papers and personal items drift past in slow arcs, older equipment 
sits beside never-activated newer systems, hand-written status labels 
on most panels, eerie melancholic atmosphere, harsh directional 
shadows from single emergency light source, desaturated with red 
practical accents
```

### Mundo Bioluminescente / Alienígena
```
Alien forest floor with towering crystalline trees, translucent 
blue-white trunks catch and refract ambient light, bioluminescent 
spores drift in slow currents through air, massive fungi emit 
soft green glow creating pool of light on forest floor, two moons 
visible through crystalline canopy, ethereal atmospheric haze, 
camera slowly pushes forward through clearing revealing impossible 
scale, wide establishing shot, purple sky visible in breaks above, 
multiple overlapping light sources create rich shadow play, 
other-worldly peaceful mystery
```

### Laboratório / Instalação Científica Operacional
```
High-tech research laboratory, modular workstation bays with 
holographic display screens showing live data, precise controlled 
white overhead lighting with no warmth, clean room aesthetic — 
smooth surfaces, sealed panels, no exposed infrastructure, 
researchers in light-colored lab coats move with purpose, 
multiple experiment rigs in various states of operation, 
one large central apparatus in active use draws the eye, 
glass partition sections create depth layers, minimal atmospheric 
elements — only ventilation system hum implied by subtle ceiling 
vents, cool 5500K clinical color temperature throughout
```

---

## 2.7 — SISTEMA DE ATMOSFERA EM 3 CAMADAS

Para efeitos atmosféricos profissionais, sempre especifique qual nível:

| Nível | Tipo | Prompt Keyword | Efeito |
|---|---|---|---|
| 1 | Haze difuso | `fine atmospheric haze` | Sonho, nostalgia, etéreo |
| 2 | Névoa com raios | `volumetric fog with defined light beams` | Mistério, drama, sagrado |
| 3 | Partículas em movimento | `dust particles floating in shafts of light` | Vida, máquinas ativas, perigo |

**Para máximo controle:** gere a atmosfera como elemento separado em fundo preto puro e composite em pós-produção com Screen/Add blending mode.

---

---

# PARTE 3 — COSTUME & WARDROBE BIBLE

## 3.1 — PRINCÍPIO FUNDAMENTAL

> O vestuário é a segunda face do personagem. Um outline ou silhueta reconhecível comunica identidade antes de qualquer detalhe facial.

Defina a SILHUETA antes de qualquer detalhe de superfície. A silhueta é reconhecível à distância e em contra-luz — é a identidade visual mais fundamental.

---

## 3.2 — TEMPLATE DE FIGURINO

```
=== FICHA DE FIGURINO ===

PERSONAGEM: [NOME]
NOME DO LOOK: [Ex: INFILTRATOR COMBAT SUIT — Script Day 01]
SCRIPT DAY: [SD01] CHANGE: [01]

--- DOCUMENTAÇÃO PARA CONTINUIDADE ---

LISTA COMPLETA DE PEÇAS (Dressing List):
1. [Jaqueta tática preta fosca — Anotação: sempre aberta, sem fecho]
2. [Camiseta base antracite sob a jaqueta]
3. [Calça cargo cinza escuro com reforço nos joelhos]
4. [Botas de couro marrom envelhecido, altura tornozelo]
5. [Coldre de coxa esquerda com fixação dupla]
6. [Relógio vintage de metal escovado, pulso esquerdo]

COMO VESTIR (Notas de Continuidade):
- Jaqueta: sempre desabotoada, gola para cima
- Camiseta: sempre por dentro da calça
- Botas: primeiro cordão sempre levemente afrouxado
- Relógio: face voltada para dentro do pulso (hábito do personagem)

AÇÕES QUE AFETAM O FIGURINO:
- Cena de chuva: jaqueta escurece uniformemente, cabelo colapsa
- Pós-combate: sangue no ombro direito, rasgo no cotovelo esquerdo
- Cena de infiltração: jaqueta removida, apenas camiseta

--- ESPECIFICAÇÕES TÉCNICAS DE MATERIAL ---

JAQUETA:
- Material: brushed nylon shell, matte finish, non-reflective
- Cor: #2C2C2C near-black with slight warm undertone
- Textura: subtle ripstop weave visible at close range
- Hardware: matte black plastic buckles, no metal shine
- Desgaste atual: worn at collar and cuffs, slight fading at shoulders
- Comportamento em movimento: stiff at shoulders, relaxed below

CALÇA:
- Material: durable cotton-nylon blend, matte
- Cor: #3A3A3A dark charcoal
- Textura: canvas-like weave
- Hardware: D-ring at belt loop right side, brass — oxidized
- Desgaste atual: reinforced knees showing double-ply stitching

BOTAS:
- Material: full-grain leather, aged 5+ years
- Cor: #5C3D2E dark cognac, unpolished
- Textura: natural grain with crease lines from wear
- Hardware: matte brass buckle, verdigris forming at edges
- Sola: black rubber, thick, worn at heel right more than left

--- PALETA GERAL DO LOOK ---
- Base: #2C2C2C / #3A3A3A (escuros neutros)
- Acento: #5C3D2E (couro marrom)
- Metal: #8B7355 (latão oxidado)
- Proibido: qualquer brilhante, qualquer cor quente além do couro

--- PROMPT LOCK (copiar idêntico em todos os prompts desta roupa) ---

WARDROBE ANCHOR:
"wearing matte black tactical jacket open at collar, dark charcoal 
cargo pants with reinforced knees, worn dark cognac leather boots 
with oxidized brass buckle, left thigh holster, vintage metal 
wristwatch face-in on left wrist, no shine on any surface, 
worn authentic appearance"

--- REFERÊNCIAS VISUAIS ---
- Front view com roupa: [URL]
- Side view com roupa: [URL]
- Back view com roupa: [URL]
- Close-up de detalhe único: [URL]
- Roupa em uso/ação: [URL]

--- HISTÓRICO DE DESGASTE (para continuidade narrativa) ---
SD01: estado base — usado mas mantido
SD05: ombro direito com sangue (cena do confronto)
SD08: rasgo no cotovelo esquerdo, sangue seco
SD12: lavado, mas mancha permanente no ombro direito visível
SD20: jaqueta irreparável, substituída por novo look

=== FIM DA FICHA DE FIGURINO ===
```

---

## 3.3 — BIBLIOTECA DE MATERIAIS PARA AI (Prompts de Textura)

### METAIS

**Cromado / Polido (armadura de elite):**
```
highly polished chrome armor plating, mirror-like reflective surface, 
specular highlights capture environment reflections, sharp edge 
definition, premium aerospace alloy finish, studio lighting 
emphasizing perfect reflections, ultra-realistic surface detail, 
fingerprints visible at closest edges
```

**Titânio Fosco (tático / militar):**
```
matte brushed titanium armor plating, non-reflective anti-glare 
surface treatment, subtle micro-texture from brushing direction, 
military-grade anodized finish in #2B3A42 slate, screw heads 
visible at panel joins, slight sheen only at extreme edge highlights
```

**Battle-Worn (combate extenso):**
```
battle-worn armor plating, deep scratch marks revealing bare 
metal beneath paint, plasma scoring from energy weapons on chest, 
emergency field repairs with mismatched sealant at crack lines, 
color variation from UV exposure — faded at exposed surfaces, 
worn edge paint showing underlying gray primer, one pauldron 
bearing a battle honor — dented but intentionally kept
```

**Ferro Forjado (fantasia / medieval):**
```
hand-forged iron plate armor, visible hammer marks on surface, 
slight irregularities confirming hand-crafting, scale pattern 
riveted construction, dark grey-black finish with slight blue tint 
from quenching, rust bleeding at joints and rivet holes — structural 
but not catastrophic, edge sharpness inconsistent from field 
resharpening
```

### COURO

**Envelhecido Autêntico:**
```
aged full-grain leather, dark brown #3D2B1F with natural patina 
development, crease lines at flex points from years of wear, 
natural color variation — darker at weathered areas, lighter at 
wear points, subtle grain visible, no conditioning in recent 
years — slightly dry surface, honest wear tells story of use
```

**Tático Moderno:**
```
tactical nylon-backed leather, smooth matte surface, uniform 
#1C1C1C near-black finish, precision stitching at stress points, 
no decorative elements, scuff marks at contact points from 
equipment and surfaces, functional not aesthetic
```

### TECIDOS AVANÇADOS

**Armadura Sci-Fi Composta:**
```
carbon-fiber weave tactical undersuit, hexagonal mesh pattern, 
slight iridescence under directional light only, form-fitting 
athletic cut, reinforced stitching panels at shoulder and 
knee stress points, moisture management texture visible 
at close range, #0A0A0F near-black with subtle structural sheen
```

**Seda / Tecido de Status:**
```
heavy silk garment, deep #4A0E2A burgundy with natural luster 
that moves with fabric, subtle woven texture visible at close range, 
draping that follows physics — pools at floor, catches light 
at crests of folds, hand-embroidered details in gold thread 
at collar and cuffs only
```

---

## 3.4 — ARMADURA SCI-FI — SISTEMA DE DESIGN

### Hierarquia de Design: Silhueta Primeiro

1. **Silhueta:** Definir a forma geral antes de qualquer detalhe
2. **Proporção:** Largura de ombro vs quadril, altura total
3. **Geometria de plano:** Angular vs orgânico, facetas vs curvas
4. **Material base:** Qual superfície domina
5. **Detalhe funcional:** O que cada parte protege / serve
6. **Desgaste e história:** O que aconteceu com esta armadura

### Template de Prompt — Armadura Sci-Fi Completa

```
[PERSONAGEM], wearing elite [TIPO: combat/infiltration/ceremonial] 
powered exosuit — 

Silhouette: [broad shoulders 1.5x hip width / compact close-fitting / 
hulking massive] overall build —

Chest: [matte/polished/composite] primary chest plate, [EMBLEMA/DETALHE] 
at center, [MATERIAL] finish, [CONDIÇÃO: pristine/battle-worn/field-repaired] —

Shoulders: asymmetric pauldrons — [DESCRIÇÃO R/L], [rank marking location] —

Arms: articulated vambrace assembly, exposed joint mechanics at elbow, 
[DETALHE: serial number / battle damage / modification] visible —

Legs: greave and cuisses system with [knee reinforcement style], 
movement-enabling articulation at joints —

Helmet: [se presente] [VISEIRA: open/closed/damaged], 
[DETALHE: HUD glow / comms array / damage] —

Material dominant: [MATERIAL COMPLETO COM ACABAMENTO] —

Lighting interaction: [como a armadura reage à luz da cena] —

[Ambiente e pose]
```

### Prompt Negativo para Armadura

```
unrealistic physics, floating elements, non-functional design, 
impossible joints, generic sci-fi armor, video game aesthetic 
(unless intentional), uniform wear pattern, no articulation points, 
shiny plastic look, weightless appearance
```

---

## 3.5 — ENVELHECIMENTO DE FIGURINO

O desgaste do figurino deve contar uma história — não apenas parecer "usado":

**Categorias de desgaste a especificar:**

| Tipo | Onde aparece | Prompt keyword |
|---|---|---|
| Uso diário | Cotovelos, joelhos, gola, punhos | `wear at high-flex and contact points` |
| Combate corpo-a-corpo | Ombros, antebraços, tornozelos | `impact scratches at offensive contact areas` |
| Armas de energia | Tórax, ombro expostos | `plasma scoring, carbon discoloration` |
| Exposição solar | Superfícies superiores | `UV fading at upper surfaces, original color preserved underneath` |
| Reparos de campo | Qualquer dano anterior | `field-repaired with available materials — mismatched but functional` |
| Orgânico/Biológico | Juntas de ventilação | `biological staining at ventilation ports` |

---

---

# PARTE 4 — MASTER PROMPT SYSTEM

## 4.1 — ESTRUTURA DEFINITIVA DE PROMPT PARA IMAGEM

### Fórmula dos 9 Elementos (ordem obrigatória)

```
[1. CÂMERA] + [2. LENTE + ASPECT RATIO] + [3. FONTE DE LUZ] + 
[4. PALETA COM HEX] + [5. COMPOSIÇÃO] + [6. SUJEITO PRINCIPAL] + 
[7. AÇÃO / POSE] + [8. ATMOSFERA + CENÁRIO] + [9. REFERÊNCIA ESTÉTICA]
```

**Exemplo completo — Hero Shot Sci-Fi:**
```
[Sony FX3 4K cinema camera] 
[Sigma Art 35mm T1.4 anamorphic, 2.39:1 aspect ratio] 
[neon magenta backlight from right, cyan fill from left, 
deep shadow base occupying 70% of frame] 
[#8B00FF deep violet shadows, #00FFFF cyan neon, 
#FF00AA magenta accents, #0D0D1A near-black base] 
[low angle hero composition, subject at left rule-of-thirds, 
rain-slicked ground reflection creates visual symmetry] 
[Kael Dawnforge, bronze-skinned warrior, mid-30s, amber eyes 
with vertical scar above left eyebrow, battle-worn obsidian armor] 
[stands facing camera, slight lean forward, hand resting on weapon] 
[rain-soaked cyberpunk alley, neon signs out-of-focus background, 
volumetric fog at ankle level, steam from grates] 
[Roger Deakins cinematography, Denis Villeneuve direction, 
Blade Runner 2049 palette, anamorphic lens flare from right source] 
photorealistic, film grain, 8K
```

---

## 4.2 — ESTRUTURA DEFINITIVA DE PROMPT PARA VÍDEO

### Fórmula dos 7 Elementos (ordem obrigatória)

```
[1. MOVIMENTO DE CÂMERA] + [2. SUJEITO + IDENTIDADE] + 
[3. AÇÃO ESPECÍFICA E SIMPLES] + [4. AMBIENTE] + 
[5. ILUMINAÇÃO] + [6. ESTILO CINEMATOGRÁFICO] + 
[7. TOM EMOCIONAL + TÉCNICO]
```

**Regra de ouro para vídeo:** Ações SIMPLES e CURTAS. Nunca: "corre, salta, gira e sorri". Sempre: "slight head turn to right, blink, subtle smile forming".

**Exemplo completo:**
```
[Slow dolly-in from medium to close-up] 
[Kael Dawnforge, bronze-skinned, amber eyes, scar above left eyebrow, 
obsidian armor, same character from reference image] 
[raises head slowly, gaze shifting from ground to camera, 
single blink, jaw sets with resolve] 
[rain-soaked alley, neon reflections on wet cobblestone, 
steam from grate at left] 
[magenta neon backlight from right creating rim outline, 
cyan fill from left, puddle reflection below] 
[cinematic film grain, anamorphic lens look, 
Blade Runner 2049 aesthetic] 
[melancholic determination, quiet menace, photorealistic, 
24fps, 5-8 seconds]
```

---

## 4.3 — BIBLIOTECA DE KEYWORDS POR CATEGORIA

### Planos Cinematográficos

| Sigla | Nome | Quando usar | Prompt exact |
|---|---|---|---|
| ELS | Extreme Long Shot | Escala épica, isolamento | `extreme wide establishing shot, vast landscape, tiny human figure` |
| LS | Long Shot | Personagem no contexto | `full body long shot, environmental context visible` |
| MS | Medium Shot | Diálogo, ação cotidiana | `medium shot waist up, eye level` |
| MCU | Medium Close-Up | Emoção + contexto | `medium close up chest to head, rule of thirds eye placement` |
| CU | Close-Up | Emoção intensa | `extreme close up portrait, fill the frame face, skin texture visible` |
| ECU | Extreme Close-Up | Detalhe, tensão máxima | `extreme macro close up, fill frame completely, no background visible` |
| OTS | Over The Shoulder | Diálogo / perspectiva | `over-the-shoulder shot, foreground character out of focus` |
| POV | Point of View | Imersão, tensão | `first-person POV, hand visible at bottom of frame` |
| BIRD | Bird's Eye | Deus, distância | `overhead bird's eye view, directly above, subjects small` |

### Movimentos de Câmera

| Movimento | Efeito | Prompt keyword |
|---|---|---|
| Dolly In (Push In) | Intensidade crescente, revelação | `slow dolly push-in, camera physically advances` |
| Dolly Out (Pull Out) | Isolamento, distanciamento | `slow dolly pull-out, camera physically retreats` |
| Pan (Horizontal) | Reveal de espaço, acompanhar | `smooth pan left/right, horizontal rotation` |
| Tilt | Reveal de escala, poder | `slow tilt up revealing scale / tilt down` |
| Tracking Shot | Acompanhar personagem | `tracking shot follows subject, maintaining frame` |
| Crane / Jib | Drama, grandiosidade | `crane shot rising/descending, vertical movement` |
| Aerial / Drone | Escala épica, contexto | `aerial drone shot, sweeping establishing` |
| Steadicam | Fluidez, imersão | `smooth steadicam follow, floating stability` |
| Handheld | Urgência, realismo | `handheld with slight natural movement, organic feel` |
| FPV | Imersão extrema | `FPV first person immersive, high-speed dynamic` |
| Static / Locked | Contemplação, tensão | `locked down tripod shot, no camera movement` |
| Crash Zoom | Impacto súbito | `rapid crash zoom in, sudden scale change` |

### Iluminação por Mood

| Setup | Prompt exact | Uso |
|---|---|---|
| Golden Hour | `warm golden backlight, soft defined shadows, amber highlights, lens flare from low sun` | Esperança, memória, fim |
| Chiaroscuro | `single hard light source from top-left, 70% shadow coverage, one catchlight in eye` | Drama, segredo, moral ambígua |
| Neon Cyberpunk | `neon magenta and cyan rim lighting, urban night reflections, wet surface glow` | Sci-fi, tensão urbana |
| Blue Hour | `cool desaturated blue-silver ambient, soft rim light, nocturnal stillness` | Tristeza, quietude, isolamento |
| Hard Desert Sun | `harsh overhead direct sun, bleached highlights, deep under-eye shadows` | Hostilidade, exposição |
| Firelight | `warm flickering orange fire source, dancing shadow movement, intimate warmth` | Humanidade, perigo primitivo |
| Diffused Overcast | `soft even diffused light, no harsh shadows, natural skin rendering` | Documentário, honestidade |
| Venetian Blinds | `parallel light strips from shuttered window, film noir striped shadow pattern` | Suspense, noir, armadilha |

### Paletas Cinematográficas Prontas

| Gênero | Highlights | Shadows | Mood | Referência |
|---|---|---|---|---|
| Action/Thriller | Orange #FF6B35 | Teal #1A5276 | Desaturado | Mad Max, John Wick |
| Sci-Fi Noir | Amber #CC8800 | Deep Blue-Purple #1A0A3D | Escuro | Blade Runner 2049 |
| Romance/Drama | Warm Gold #FFD700 | Soft Lavender #9B8BB4 | Suave | La La Land |
| Horror | Cold White #E8F4F8 | Desaturated Green #1A2918 | Drenado | The Witch |
| Epic Fantasy | Rich Orange #CC6600 | Royal Blue #003366 | High contrast | LOTR |
| Indie/Naturalist | Muted tones, analog grain | Warm shadow #3D2B1F | Orgânico | Moonlight |
| Solarpunk/Utopia | Golden #FFE066 | Soft green #4A7C59 | Luminoso | Oasis |

---

## 4.4 — COMPOSIÇÃO: 15 TÉCNICAS ESSENCIAIS

| Técnica | Quando usar | Prompt keyword |
|---|---|---|
| Rule of Thirds | 80% dos casos | `rule of thirds, subject at right/left intersection` |
| Negative Space | Isolamento, épico | `vast negative space, subject small against environment` |
| Framing within Frame | Reforço de confinamento | `natural frame using archway/doorway/window` |
| Leading Lines | Guiar o olhar | `leading lines from foreground converging to subject` |
| Dutch Angle | Caos, desequilíbrio | `dutch angle 15 degrees, tilted horizon` |
| Symmetry | Wes Anderson, poder | `perfect bilateral symmetry, centered composition` |
| Three-Layer Depth | Profundidade cinematográfica | `foreground element, midground subject, background environment` |
| Low Angle Hero | Dominância, herói | `extreme low angle, looking up at subject, heroic` |
| High Angle Victim | Vulnerabilidade | `high angle looking down, subject small in frame` |
| Fill the Frame | Intensidade máxima | `fill the frame, subject occupies entire image space` |
| S-Curve | Elegância, fluxo | `S-curve composition, subject follows natural curve` |
| Golden Ratio | Equilíbrio natural | `golden spiral composition, Fibonacci balance` |
| Breaking Pattern | Ponto focal imediato | `repeating pattern broken by single anomaly subject` |
| Juxtaposition | Comentário, contraste | `opposing elements side by side creating meaning` |
| Scale Contrast | Épico, sublime | `scale contrast — tiny human figure against massive environment` |

---

## 4.5 — NEGATIVE PROMPTS DEFINITIVOS

### Negative Prompt Master (Imagem — usar sempre)

```
bad anatomy, extra limbs, missing fingers, wrong number of fingers, 
distorted face, asymmetric face (unless intentional), blurry, 
low quality, jpeg artifacts, watermark, text overlay, signature, 
overexposure, blown highlights, flat lighting, amateur photography, 
cartoon style, anime style, illustration, painting, 3d render, 
cgi plastic look, waxy skin, poreless skin, dead eyes, 
oversaturation, instagram filter, HDR overprocessed, 
artificial skin smoothing, bad hands, deformed hands, 
inconsistent character features, wrong eye color, 
age variation from established, outfit change
```

### Negative Prompt Master (Vídeo — usar sempre)

```
flickering, temporal inconsistency, jitter, motion artifacts, 
static noise, frame inconsistency, shaky footage (unless handheld 
specified), low resolution, blurry motion, distorted faces, 
watermark, text overlays, inconsistent lighting, character drift, 
wrong outfit, wrong eye color, wrong hair, morphing body, 
extra limbs, deformed anatomy, unnatural physics, 
cartoon style, animated style (unless intentional)
```

### Negative Prompt para Aging Específico

```
different eye color, different face shape, changed nose structure, 
altered bone structure, inconsistent distinctive features, 
cartoonish wrinkles, flat artificial aging, plastic surgery appearance, 
uncanny smoothness in wrong age, uniform wrinkle distribution, 
identity shift, different person, anachronistic clothing
```

---

## 4.6 — EXEMPLOS PRONTOS PARA USAR

### Portrait Hero Cinematográfico

```
Cinematic medium close-up portrait of [PERSONAGEM], rule of thirds 
eye placement at left intersection, Chiaroscuro lighting with 
single hard source from top-left, deep shadow covers 70% of face, 
single catchlight in left eye, skin texture visible with subsurface 
scattering at cheek, teal and orange color grade, shallow depth 
of field with anamorphic oval bokeh, shot on ARRI Alexa 35mm, 
subtle film grain, photorealistic, 8K resolution

NEGATIVE: (worst quality, low quality:1.4), (blurry:1.2), 
(cartoon, anime, illustration:1.4), 3d render, plastic skin, 
waxy skin, poreless skin, bad anatomy, dead eyes, text, watermark
```

### Establishing Shot Épico

```
Extreme wide establishing shot, [LOCALIZAÇÃO DESCRITA], 
tiny silhouette of [PERSONAGEM] at bottom third foreground, 
three distinct depth layers: detailed foreground, atmospheric 
midground, hazy distant background, rule of thirds horizon line, 
volumetric light through atmospheric haze, golden ratio 
compositional balance, anamorphic 2.39:1 aspect ratio, 
[PALETA DA CENA], [REFERÊNCIA CINEMATOGRÁFICA], 
cinematic masterpiece, photorealistic, 8K

NEGATIVE: (low quality:1.3), blurry, cartoon, illustration, 
fake sky, text, watermark
```

### ECU Emocional

```
Extreme close-up portrait of [PERSONAGEM], fill the frame, 
skin texture visible — pores, fine lines, subtle imperfections, 
subsurface scattering in lips and nose, single sidelight 
from left creating rim on right cheek, [COR DOS OLHOS] iris 
detail fully visible, [EXPRESSÃO ESPECÍFICA: slight tremor 
in lower lip / determination hardening in jaw / tears forming 
without falling], anamorphic bokeh background, film grain, 
photorealistic, ultra-high resolution

NEGATIVE: (blurry:1.3), low resolution, cartoon, plastic skin, 
poreless skin, fake expression, bad anatomy, text
```

---

---

# PARTE 5 — AUDIO & SOUND BIBLE

## 5.1 — HIERARQUIA DE MIXAGEM CINEMATOGRÁFICA

A hierarquia de volumes define o que o espectador ouve conscientemente:

```
HIERARQUIA DE VOLUME (dB relativo):

1. DIÁLOGO / VOICEOVER    0 dB (referência)
2. SFX PRIMÁRIOS         -6 dB a -8 dB
3. FOLEY / SFX AMBIENTE  -12 dB a -15 dB
4. TRILHA MUSICAL        -18 dB a -22 dB durante fala
5. AMBIÊNCIA / BED       -20 dB a -25 dB

REGRA: música sobe para 0 dB apenas quando NÃO há diálogo.
ERRO FATAL: colocar música e voz em volumes similares.
```

---

## 5.2 — TARGETS DE LOUDNESS POR DESTINO

| Destino | Padrão | LUFS Target | Sample Rate |
|---|---|---|---|
| YouTube / Streaming | ITU-R BS.1770 | -14 LUFS | 48kHz |
| Broadcast Europeu | EBU R128 | -23 LUFS | 48kHz |
| Broadcast Americano | ATSC A/85 | -24 LUFS | 48kHz |
| Cinema DCP | SMPTE | -20 LUFS | 48kHz |
| Podcast | Recomendado | -16 LUFS | 44.1kHz |
| Entrega de produção | Sempre | WAV 24-bit | 48kHz |

**NUNCA entregar MP3 para broadcast ou qualquer projeto com etapas adicionais de encoding.**

---

## 5.3 — SOUND DESIGN SCI-FI — SISTEMA DE 5 CAMADAS

Para qualquer ambiente ou efeito sci-fi, construa em camadas:

| Camada | Frequência | Conteúdo | Propósito |
|---|---|---|---|
| 1 — Base/Sub | 20-80 Hz | Sub-bass profundo, drones baixos | Peso, presença, poder |
| 2 — Corpo | 80-500 Hz | Texturas metálicas, síntese FM | Caráter, identidade do som |
| 3 — Ar/Espaço | 500Hz-4kHz | Reverb de câmara, delays controlados | Espaço, profundidade |
| 4 — Detalhes | 4kHz-8kHz | Micro-sons de interface, servos | Detalhe, realismo |
| 5 — Ambiência | 20Hz-20kHz | Ruído de fundo amplo, sistemas | Vida no ambiente |

**Princípio criativo:** `O familiar processado de forma não familiar`. Sons cotidianos (geladeira, computador, motor) processados com pitch extreme + flanger + reverb espacial criam ambiências futuristas convincentes.

---

## 5.4 — WORKFLOW DE ÁUDIO PARA COMERCIAL (Ordem obrigatória)

1. **Voiceover primeiro** — ElevenLabs v3 com audio tags para controle preciso
2. **Trilha musical segundo** — duração exata correspondente ao vídeo
3. **SFX específicos por cena** — 5 variações por efeito, nunca repetir o mesmo arquivo
4. **Ambiência / Bed** — loop que sustenta todo o comercial
5. **Mixagem final** — aplicar hierarquia de volumes
6. **Mastering** — iZotope Ozone ou LANDR conforme destino
7. **Stems separados** — exportar cada camada individualmente

---

## 5.5 — PROMPTS DE MÚSICA CINEMATOGRÁFICA

### Estrutura Master para Suno V6 / ElevenLabs Music

```
[GÊNERO PRINCIPAL], [SUBGÊNERO], [INSTRUMENTOS PRINCIPAIS], 
[MOOD / EMOÇÃO], [BPM], [DURAÇÃO EM SEGUNDOS], 
[VOCAL / INSTRUMENTAL], [CONTEXTO DE USO]
```

### Templates por Mood / Uso

**Sci-Fi Épico (Abertura / Clímax):**
```
Epic orchestral sci-fi soundtrack, hybrid electronic, sweeping 
strings and brass with synth pads and choir, triumphant and 
awe-inspiring, 110 BPM, 90 seconds, instrumental only, 
building from quiet ambient opening to massive orchestral climax 
at 60 second mark, commercial brand reveal moment
```

**Sci-Fi Suspense (Tensão / Infiltração):**
```
Sci-fi thriller cue, pulsing synth bass, tense minimal orchestra, 
futuristic suspense, rising tension build, 80 BPM, 60 seconds, 
no vocals, percussion enters at 30 second mark, 
never resolves — maintains tension throughout, 
stealth mission aesthetic
```

**Emocional / Drama:**
```
Emotional storytelling score, solo piano melody, 
warm string ensemble entering at 15 seconds, 
melancholic but hopeful, 65 BPM, 75 seconds, 
no vocals, single peak dynamic moment at 50 seconds, 
resolves gently, cinematic commercial underscore
```

**Ação / Perseguição:**
```
Intense action score, rapid driving strings, pounding 
percussion, explosive cinematic energy, modern hybrid 
orchestral with electronic elements, punching brass hits, 
140 BPM, 45 seconds, instrumental, building to massive 
final moment at last 10 seconds, trailer music energy
```

**Ambiente / Ambiência Futurista (Stable Audio):**
```
Futuristic ambient soundscape, metallic resonance, 
sub-bass frequencies 40-80Hz, digital glitch textures, 
electronic hum with organic variations, industrial 
space environment, 3 minutes, no melody, 
loop-ready, 44.1kHz WAV
```

---

## 5.6 — PROMPTS DE VOICEOVER (ElevenLabs)

### Configurações Técnicas

| Parâmetro | Valor para Naturalidade | Valor para Drama |
|---|---|---|
| Stability | 50-60% | 65-75% |
| Similarity | 75-80% | 80-90% |
| Style Exaggeration | 15-25% | 30-40% |
| Speaker Boost | ON sempre | ON sempre |

### Design de Voz por Arquétipo

**Narrador Cinematográfico (autoridade):**
```
Deep authoritative male voice, 45-55 years, broadcast quality, 
gravitas without aggression, warm resonance in lower mid-range, 
measured deliberate pacing, slight breathiness on consonants, 
cinematic trailer narrator energy
```

**Personagem Sci-Fi / AI:**
```
Synthetic AI entity voice, androgynous, clear precise articulation, 
subtle digital processing layered underneath organic tone, 
confident intelligent character, 30s energy, 
warm enough to be trusted, not cold
```

**Personagem Jovem / Relatable:**
```
Natural conversational voice, late 20s, genuine warmth, 
slight regional texture without being distracting, 
energy of someone talking to a friend, 
not announcer — person
```

### Audio Tags XML (ElevenLabs v3)

```xml
Apresentando [pause 0.5s] o futuro de tudo que você conhece.
[breathe] [emphasis]CineForge[/emphasis] — 
onde imaginação [pause 0.3s] se torna 
[whisper]realidade.[/whisper]
```

---

## 5.7 — PROMPTS DE SFX (ElevenLabs Sound Effects)

**Regra de uso:** Gere sempre 5 variações por efeito. Nunca use o mesmo arquivo duas vezes na mesma cena.

**Nave espacial — start-up:**
```
Futuristic spaceship engine powering up sequence, 
begins with low sub-bass rumble building over 2 seconds, 
transitions to mid-range mechanical whir, 
peaks with high-frequency plasma drive whine at 3 seconds, 
cuts to steady operational hum, 4 seconds total, 
cinematic sci-fi aesthetic, rich harmonic content
```

**Interface holográfica — ativação:**
```
Holographic interface activation sequence, 
crisp digital ascending tone cluster, 
high-frequency harmonic shimmer, 
digital texture throughout, 
1.5 seconds, resolves with clean sustained note, 
futuristic UI sound design
```

**Portal / Warp — abertura:**
```
Sci-fi portal opening effect, initial spatial distortion sound, 
deep bass bloom building, warping harmonic content, 
high-frequency energy shimmer at peak, 
dissipates with lingering resonance, 
5 seconds total, powerful and awe-inspiring
```

**Explosão cinematográfica:**
```
Cinematic explosion with physical impact character, 
initial sharp transient crack, low-frequency bass bloom 
extending 1.5 seconds, debris scatter texture, 
distant reverb tail extending 3 seconds, 
natural exponential decay, 5 seconds total
```

---

---

# PARTE 6 — VFX & EFFECTS BIBLE

## 6.1 — PRINCÍPIO FUNDAMENTAL DO COMPOSITING

> **REGRA DE OURO VFX:** Nunca gere efeitos luminosos (névoa, glow, hologramas, partículas, energia) diretamente na cena final em uma única geração. Gere o efeito em fundo preto puro (pure black background), depois composite usando Screen ou Add blending mode.

Isso oferece:
- Controle total de posicionamento
- Controle de intensidade via opacidade
- Colorização independente
- Possibilidade de looping
- Reutilização em múltiplas cenas

---

## 6.2 — EFEITOS HOLOGRÁFICOS — WORKFLOW COMPLETO

### Geração do Elemento Holográfico

```
Translucent holographic data interface materializes from center 
outward with geometric ripple pattern, hexagonal grid overlays 
float in layers at slight depth variation, soft blue-white energy 
with subtle cyan edge refraction, luminescent particles orbit 
central data structure, surface wobbles like liquid membrane 
when activated then stabilizes to clean geometry, energy lines 
pulse along hexagonal edges in rhythmic sequence, 

PURE BLACK BACKGROUND — screen compositing ready, 
no foreground subjects, isolated element, 
sci-fi aesthetic, high detail
```

### Pipeline de Compositing

1. Gere hologramaai em fundo preto puro
2. No After Effects ou DaVinci Fusion: importe como camada acima do footage
3. Blending mode: **Screen** (remove o preto, mantém as luzes)
4. Color Correction: ajuste Hue/Saturation para combinar com iluminação da cena
5. Reduza opacidade para 70-85% para aspecto translúcido realista
6. Adicione leve motion blur se a cena tiver movimento

---

## 6.3 — EFEITOS DE NÉVOA E FUMAÇA

### Tipos de Névoa por Efeito Visual

| Tipo | Prompt | Uso |
|---|---|---|
| Ground fog (seca) | `dry ice fog, ground-hugging, low to floor, wisps barely above lower third` | Cemitério, floresta mística, horror |
| Volumetric (raios) | `volumetric fog with defined light beam shafts, god rays` | Drama, sagrado, mistério |
| Haze atmosférico | `fine atmospheric haze, diffused ambient, soft depth reduction` | Sci-fi, nostalgia, sonho |
| Fumaça de explosão | `dense billowing smoke expanding outward, turbulent cloud formation` | Ação, destruição, batalha |
| Vapor industrial | `industrial steam burst from vents, natural upward dispersion` | Cyberpunk, fábrica, corredores |

### Prompts para Compositing de Névoa

**Ground Fog para Compositing:**
```
In a pure black void, ethereal dry ice fog flows outward from 
background to foreground, remains low — ground-hugging effect, 
each wisp exceptionally sparse and translucent with delicate 
tendrils barely rising above lower third of frame, vapor emerges 
gently from depth of scene, static camera, pure white vapor 
against pitch-black background, movement peaceful and measured, 
high resolution, loop-ready if possible
```

**Névoa Volumétrica para Compositing:**
```
In a pure black void, thick volumetric fog fills frame with 
horizontal drift from left to right, broad expansive presence 
drifting in subtle waves, multiple semi-transparent layers 
create depth, static locked camera captures peaceful lateral 
drift, pure white fog against pitch black, constant and serene, 
high resolution 4K, loop-ready
```

**Fumaça de Impacto para Compositing:**
```
Create high-resolution locked video on pure black background, 
dense smoke screen expanding rapidly outward from central point, 
thick erratic cloud, dynamic movement with multiple expansion 
bursts, disperses in irregular unpredictable patterns, 
fading at edges as it fills space, professional VFX quality
```

---

## 6.4 — EFEITOS DE ENERGIA E PARTÍCULAS

### Energy Beam / Laser

```
Brilliant [blue-white / violet / green] plasma beam fires 
between two points, electrical arcs branch off main beam 
creating lightning-like secondary tendrils, intense light 
casts harsh moving shadows on surrounding surfaces, 
beam dissipates with lingering energy glow and smoke trail, 
surrounding air shimmers from heat distortion, 
multiple light layers: bright core with cooler outer glow, 
PURE BLACK BACKGROUND for compositing
```

### Force Field / Shield

```
Hexagonal energy barrier materializes from center outward 
with geometric ripple propagation, translucent [orange / blue / 
white] energy field with visible edge refraction distorting 
background, debris particles bounce off surface creating 
small impact flashes, field surface wobbles like liquid 
membrane when struck then stabilizes, energy lines pulse 
along hexagon edges rhythmically, 
PURE BLACK BACKGROUND for screen compositing
```

### Particle Systems

```
Luminescent particles orbit central vortex in complex 
choreographic patterns, each particle with individual 
trailing light wisp, pulsing energy emission from core 
attracts and repels particles, physics-based turbulence 
creates organic variation in orbit paths, particle density 
varies — dense near core, sparse at edges, 
color gradient from [COR CORE] at center to [COR EDGE] at periphery, 
PURE BLACK BACKGROUND for Add compositing
```

### Hyperspace / Warp Jump

```
Stars begin stretching into long light streaks from center 
of frame outward, acceleration effect as ship speeds up, 
colors shift from white through blue to violet showing 
light spectrum compression, geometric light tunnel forms 
from stretched starlight, extreme motion blur and radial 
lens distortion, final flash of pure white, 
energetic and dynamic, anamorphic 2.39:1
```

---

## 6.5 — NEON E GLOW — TÉCNICA PROFISSIONAL (After Effects)

### Sistema de 3 Camadas para Neon

Para cada cor de neon, criar 3 camadas separadas:

1. **Tight Glow (Núcleo):**
   - Radius: 5-8px
   - Intensity: 100%
   - Color: cor pura do neon
   - Blending: Add

2. **Medium Glow (Halo) — com flickering:**
   - Radius: 20-30px
   - Expression no opacity: `wiggle(50, 10)` para 50Hz flicker com variação de 10%
   - Color: cor do neon a 70% saturação
   - Blending: Screen

3. **Wide Glow (Difusão Ambiente):**
   - Radius: 80-120px
   - Intensity: 30-40%
   - Color: cor do neon desaturada 50%
   - Blending: Screen

### Prompt para Neon em Imagem

```
[SUJEITO] with bold neon [COR] outline, inner glow core pure [COR], 
neon light spill on surrounding wet surfaces creating color pool, 
light halation effect — glow extends 10-15% beyond physical neon source, 
lens flare from closest neon element, volumetric haze catches 
and scatters neon color, dark atmospheric background maximizes 
contrast, cinematic color grade, high contrast shadows
```

---

## 6.6 — ENVELHECIMENTO E DE-AGING EM VFX

### Para Projetos AI

1. Crie character sheet do personagem em cada idade (ver Parte 1.5)
2. Use Runway Edit Studio para morphing progressivo de textura de pele sobre imagem existente
3. Para sequência completa: use EBSynth para transferir frame-chave de idade para toda a sequência
4. ComfyUI + ControlNet FaceSwap para controle granular de aging local

### Checklist de Aging Convincente

```
[ ] Estrutura óssea preservada (não mude jaw, cheekbones, eye socket)
[ ] Cor dos olhos idêntica
[ ] Traços distintivos mantidos (cicatrizes, marcas)
[ ] Textura de pele muda gradualmente, não abruptamente
[ ] Cabelo: cor progride do original para grisalho de forma verossímil
[ ] Postura: ligeira curvatura aumenta com a idade
[ ] Expressão habitual: energia juvenil → serenidade madura → quietude sábia
[ ] Vestuário: contextualizado na época correta
[ ] Linguagem corporal reflete a idade (não apenas o rosto)
[ ] Prompt negativo específico de aging incluído
```

---

---

# PARTE 7 — COLOR BIBLE

## 7.1 — PIPELINE DE COR COMPLETO

### Regra de Ouro do Pipeline

**NUNCA** faça color grade em espaço display-referred (Rec.709 desde o início). Sempre trabalhe em scene-referred e converta apenas na saída.

```
PIPELINE CORRETO:

INPUT (LOG / RAW)
    ↓
CST (Color Space Transform) → DaVinci Wide Gamut/Intermediate
    ↓
CORREÇÃO BASE (exposição, balanço de brancos, densidade)
    ↓
COLOR GRADE CRIATIVO (mood, LUTs, paleta)
    ↓
QUALIFICADORES DE COR (isolamento de skin tones, neons, etc.)
    ↓
CST OUTPUT → Rec.709 / DCI-P3 / Rec.2020 conforme destino
    ↓
EXPORTAÇÃO
```

---

## 7.2 — PARÂMETROS TÉCNICOS DOS LOOKS PRINCIPAIS

### Look 1 — Sci-Fi Neon Cyberpunk (Blade Runner 2049)

**Lift (Sombras):**
- R: -0.04 (retirar vermelho das sombras)
- G: -0.02
- B: +0.03 (adicionar azul/ciano nas sombras)

**Gamma (Meios-tons):**
- R: -0.01
- G: +0.01 (leve verde-teal)
- B: +0.02

**Gain (Altas luzes):**
- Versão laranja: R: +0.08, G: -0.02, B: -0.05
- Versão violeta: R: +0.03, G: 0, B: +0.04

**Saturação geral:** 75-85 (base dessaturada)

**Curvas:** S-curve no Master para contraste cinematográfico

**Técnica avançada:** Use qualificadores de cor para boost de saturação nos neons sem afetar skin tones — isole os blues e magentas e sature +30 a +50 apenas nesses ranges.

### Look 2 — Golden Hour / Epic Fantasy

**Lift:** +0.01 R, 0 G, -0.01 B (morno nas sombras)
**Gamma:** +0.02 R, +0.01 G, -0.01 B
**Gain:** +0.05 R, +0.02 G, -0.03 B (dourado intenso nos highlights)

**Saturação:** 100-115 (ligeiramente mais saturado)
**Contraste:** S-curve mais agressiva que o normal

**Técnica de skin tone:** Use qualifier para isolar skin tones e aplicar lift de +0.02 R separado — pele fica dourada sem afetar o ambiente.

### Look 3 — Horror / Suspense

**Lift:** 0 R, +0.01 G, 0 B (leve verde nauseante nas sombras)
**Gamma:** -0.01 R, +0.01 G, -0.01 B
**Gain:** -0.01 R, 0 G, +0.01 B (frio nos highlights)

**Saturação:** 60-75 (fortemente dessaturado)

**Técnica:** Curve S muito agressiva nas sombras — crush os negros mais que o normal, deixe informação só na zona 10-90%.

### Look 4 — Indie / Naturalist (Analog Feel)

**Lift:** Elevado levemente (+0.02 em todos os canais) — sombras não chegam ao zero absoluto (emulação de velatura de negativo)
**Gamma:** Neutro com leve calor (+0.01 R)
**Gain:** Ligeiramente rollado nos altos — não deixe estourar completamente

**Saturação:** 85-95

**Film grain (crucial para este look):** Adicionar noise analógico, não digital.
- Grain size: 25-35
- Grain texture: luminance noise, não RGB noise
- Intensidade: 10-20 para naturalidade

---

## 7.3 — CONSISTÊNCIA DE COR ENTRE CLIPS AI

Protocolo para manter todos os clips com a mesma aparência:

1. **Selecione um "Anchor Frame":** O melhor clip gerado com o look correto é a referência
2. **Crie uma LUT 3D** desse clip (export via DaVinci Resolve → Color Space Transform node → Export as .cube)
3. **Aplique a LUT** como primeiro nó de grade em todos os outros clips
4. **Ajuste fino** em cada clip se necessário, mas a LUT garante ponto de partida idêntico
5. **Group Nodes no DaVinci:** Coloque todos os clips do mesmo ambiente no mesmo Group — mudanças afetam todos simultaneamente

### Para Prompts AI — Consistência de Cor

Inclua em TODOS os prompts de imagem/vídeo do mesmo projeto:

```
[LOOK NAME] color grade: [HIGHLIGHT COLOR HEX] highlights, 
[SHADOW COLOR HEX] shadows, [MOOD] atmosphere, 
[REFERÊNCIA DE FILME] cinematography palette, 
[TEMPERATURA] color temperature, consistent with established 
visual style of [PROJETO]
```

---

## 7.4 — LUTs RECOMENDADOS

### Gratuitos

| LUT | Uso | Fonte |
|---|---|---|
| Lutify.me Free Pack | Variedade de looks cinematográficos | lutify.me |
| SpeedLooks Free | Looks rápidos de produção | speedlooks.com |
| Koji Color Free | Emulação de película | kojicolor.co |

### Pagos (Alta Qualidade)

| LUT / Plugin | Melhor para | Preço |
|---|---|---|
| Film Convert Nitrate | Emulação analógica mais realista, grain incluído | $119 perpétuo |
| Dehancer Pro | +100 emulações de película incluindo Kodachrome/Portra | $29/mês |
| IWLTBAP | Looks cinematográficos para video digital | ~$50 |

### Criando LUTs Customizados

Ferramentas:
- **DaVinci Resolve** — Export via nó Color Space Transform (gratuito)
- **Lattice LUT Editor (Mac)** — Edição matemática precisa (~$199)
- **Omniscope** — Visualização e edição de LUTs

**Workflow de criação:**
1. Grade em imagem representativa do projeto
2. Export → .cube (33x33x33 para alta qualidade)
3. Testar em pelo menos 10 imagens diferentes de cena/iluminação variados
4. Se passou nos 10 testes, aprovar para uso em produção

---

---

# PARTE 8 — FERRAMENTAS RANQUEADAS

## 8.1 — GERAÇÃO DE VÍDEO

### Top 5 com Scoring

| # | Ferramenta | Qualidade | Consistência | Custo | Facilidade | Score |
|---|---|---|---|---|---|---|
| 1 | Google Veo 3.1 | 10/10 | 8/10 | 6/10 | 7/10 | **9.0** |
| 2 | Runway Gen-4.5 | 9.5/10 | 8.5/10 | 6/10 | 7.5/10 | **8.8** |
| 3 | Kling AI 3.0 | 9/10 | 9/10 | 8.5/10 | 8/10 | **8.8** |
| 4 | Seedance 2.5 | 8.5/10 | 9/10 | 9/10 | 8/10 | **8.5** |
| 5 | Luma Ray 3.2 | 8.5/10 | 7.5/10 | 8/10 | 8.5/10 | **8.0** |
| 6 | Sora 2 | 9/10 | 7/10 | 7/10 | 8/10 | **7.9** |
| 7 | Pika 2.2 | 7.5/10 | 7/10 | 9/10 | 9/10 | **7.5** |

### Quando Usar Cada Ferramenta de Vídeo

| Ferramenta | Use quando precisar de... |
|---|---|
| Veo 3.1 | Qualidade máxima absoluta, áudio nativo integrado, planos hero de abertura |
| Runway Gen-4.5 | Controle preciso de câmera, post-produção integrada, broadcasting comercial |
| Kling AI 3.0 | Personagens recorrentes (melhor consistência), multi-shot, física de produto |
| Seedance 2.5 | Volume alto de clips com consistência a custo-benefício máximo |
| Luma Ray 3.2 | Movimento orgânico natural, física realista (água, fogo, atletas) |
| Sora 2 | UGC style, social media, naturalidade fotorrealista |
| Pika 2.2 | Prototipagem rápida, testes de conceito, validação antes de gastar premium |

---

## 8.2 — GERAÇÃO DE IMAGEM

| # | Ferramenta | Qualidade | Consistência Personagem | Controle | Score |
|---|---|---|---|---|---|
| 1 | Midjourney V7 | 9.5/10 | 9/10 (--cref) | 7/10 | **9.0** |
| 2 | Flux Pro | 9.5/10 | 7/10 | 8/10 | **8.5** |
| 3 | DALL-E 3 / GPT Image 2 | 8.5/10 | 6/10 | 9/10 | **8.0** |
| 4 | Stable Diffusion + LoRA | 8.5/10 | 10/10 (LoRA) | 10/10 | **9.5** (técnico) |

### Quando Usar Cada Ferramenta de Imagem

| Ferramenta | Use quando precisar de... |
|---|---|
| Midjourney V7 | Character sheets, composição cinematográfica, estética artística, --cref para consistência |
| Flux Pro | Máximo fotorrealismo, cenários que parecem fotos reais |
| DALL-E 3 | Texto tipográfico na imagem, logos, slogans dentro de cenas |
| SD + LoRA | Controle absoluto, consistência matemática perfeita, pipeline local sem custo por geração |

---

## 8.3 — ÁUDIO

### Música

| # | Ferramenta | Qualidade | Licença Comercial | Versatilidade | Score |
|---|---|---|---|---|---|
| 1 | Suno V6 Pro | 9/10 | Sim (plano pago) | 10/10 | **9.0** |
| 2 | ElevenLabs Music v2.5 | 8.5/10 | Sim (Creator+) | 8/10 | **8.5** |
| 3 | Stable Audio 3.0 | 8/10 | Sim (dados licenciados) | 8/10 | **8.0** |
| 4 | AIVA Pro | 7.5/10 | Sim (MIDI incluso) | 7/10 | **7.5** |
| X | UDIO | Inacessível | PROIBIDO (out/2025) | — | **NÃO USAR** |

### Voz

| # | Ferramenta | Qualidade | Controle | Score |
|---|---|---|---|---|
| 1 | ElevenLabs v3 | 9.5/10 | 9.5/10 (audio tags) | **9.5** |
| 2 | Murf AI | 8/10 | 8/10 | **8.0** |

### SFX

| # | Ferramenta | Score |
|---|---|---|
| 1 | ElevenLabs SFX | 9/10 |
| 2 | Adobe Firefly Sound | 8/10 |
| 3 | Sonilo (frame-accurate) | 8.5/10 |

---

## 8.4 — COMPOSITING / VFX / PÓS-PRODUÇÃO

| # | Ferramenta | Nível | Quando Usar |
|---|---|---|---|
| 1 | Foundry Nuke 17 | Hollywood Studio | Feature film, episodic VFX complexo |
| 2 | Adobe After Effects | Profissional | Broadcast, advertising, motion graphics |
| 3 | DaVinci Fusion (dentro do Resolve) | Semi-profissional | Alternativa gratuita ao Nuke |
| 4 | Wonder Studio | Indie-Profissional | Substituição de ator por CGI automática |
| 5 | ComfyUI | Avançado open-source | Workflows AI VFX com controle granular |

### Color Grading

| # | Ferramenta | Score |
|---|---|---|
| 1 | DaVinci Resolve Studio | 10/10 (gratuito/pago) |
| 2 | Adobe Premiere Lumetri | 8/10 (integração CC) |

### Upscale de Vídeo

| # | Ferramenta | Score |
|---|---|---|
| 1 | Topaz Video AI Astra | 9.5/10 |

---

## 8.5 — WORKFLOW IDEAL COMBINANDO FERRAMENTAS

### Workflow Padrão — Produção Cinematográfica AI Completa

```
FASE 1 — PRÉ-PRODUÇÃO

Script/Roteiro
    → Claude / ChatGPT para refinamento e character bibles
    → Storyflow para organizar visualmente

Character Sheets
    → Midjourney V7 --cref para turnaround sheets
    → 4 ângulos em iluminação neutra, fundo branco

Storyboard
    → Storyboarder.ai (com personagens consistentes)
    → Frames cinemáticos no Midjourney para Director's Treatment

---

FASE 2 — PRODUÇÃO (por tipo de cena)

CENAS COM PERSONAGENS RECORRENTES:
    → Kling AI 3.0 Elements (melhor consistência)
    → Input: character sheet como referência
    → Output: clips 5-8 segundos

CENAS HERO / ALTA QUALIDADE:
    → Runway Gen-4.5 (melhor controle cinematográfico)
    → Input: imagem âncora do personagem

CENAS COM ÁUDIO NATIVO (diálogo):
    → Google Veo 3.1
    → Ingredients to Video com referências

PROTOTIPAGEM / TESTES:
    → Pika 2.2 (custo zero para validação)

---

FASE 3 — ÁUDIO

Voiceover:
    → ElevenLabs v3 com audio tags

Trilha Musical:
    → Suno V6 Pro para músicas com vocais
    → ElevenLabs Music v2.5 para scoring instrumental

SFX:
    → ElevenLabs SFX (5 variações por efeito)
    → Sonilo para posicionamento frame-accurate automático

---

FASE 4 — PÓS-PRODUÇÃO

Efeitos Atmosféricos:
    → Kling 1.5 Pro via ComfyUI (névoa/partículas em fundo preto)
    → Composite no AE / Fusion com Screen/Add blending

Upscale:
    → Topaz Video AI Astra → 4K broadcast quality

Color Grade:
    → DaVinci Resolve Studio
    → Pipeline: LOG → Wide Gamut → Grade → Rec.709 output

Montagem Final:
    → DaVinci Resolve ou Adobe Premiere Pro
    → Stems separados: música / voiceover / SFX / ambiência

Entrega:
    → H.264/H.265 para digital
    → ProRes 4444 para broadcast
    → WAV 48kHz/24-bit para áudio de entrega
```

---

---

# PARTE 9 — 50 REGRAS DE OURO

## BLOCO A — CHARACTER CONSISTENCY (Regras 1-10)

**REGRA 1 — Nunca text-to-video para personagens recorrentes**
Gere sempre via image-to-video com imagem âncora do personagem. Sem a âncora, o AI inventa uma nova estrutura óssea e face em cada cena. O texto descreve, a imagem ancora.

**REGRA 2 — Create Once, Lock Identity, Reuse Reference**
O character sheet gerado no início da produção é o documento mais importante da Bible. Tudo parte dele. Nenhuma cena começa sem referência ao character sheet aprovado.

**REGRA 3 — 2-3 imagens de referência, nunca 6+**
Seis imagens de referência se médiam — o resultado é um personagem sem identidade forte. Duas ou três imagens limpas, iluminação neutra, fundo simples, são sempre superiores a seis moody shots.

**REGRA 4 — Nome fictício único = âncora semântica**
"O guerreiro" vs "Kael Dawnforge" — o nome único cria uma âncora semântica que reduz ambiguidade. Invente um nome específico para cada personagem antes de qualquer geração.

**REGRA 5 — Mesmas palavras, mesma ordem, para sempre**
"Dark brown hair with copper highlights" em todos os prompts. Se um prompt diz "chocolate locks" e outro "auburn hair", o AI interpreta diferentes personagens. O vocabulário é imutável.

**REGRA 6 — Clips curtos, 5-8 segundos, sempre**
Clips longos aumentam o character drift exponencialmente. Gere em bursts curtos e junte no editor. 8 segundos de perfeição vale mais que 30 segundos de drift progressivo.

**REGRA 7 — Frame chaining entre cenas**
Capture o último frame de um clip e use como primeiro frame do próximo. Cria continuidade visual seamless sem necessidade de tools especiais.

**REGRA 8 — Treine LoRA para 20+ cenas**
Para produção com mais de 20 cenas do mesmo personagem, um LoRA é obrigatório. O investimento de 30-60 minutos de treino se paga na segunda cena gerada. Sem LoRA, o retrabalho acumulado é garantido.

**REGRA 9 — Aspect ratio idêntico em toda a produção**
Mudar de 16:9 para 9:16 força o modelo a re-enquadrar o personagem e introduz inconsistências. Defina o aspect ratio no início e nunca mude.

**REGRA 10 — Color grading une o que gerações separam**
Clips de diferentes batches de geração têm temperaturas de cor e contraste diferentes. Um personagem perfeitamente consistente ainda parecerá diferente entre cenas sem color matching. DaVinci Resolve + LUT baked = solução.

---

## BLOCO B — AGING & REJUVENESCIMENTO (Regras 11-15)

**REGRA 11 — Staged progression, nunca salto único**
Jovem para idoso em um único prompt = aparência cartunesca. Use 4-6 estágios intermediários. O envelhecimento convincente é gradual.

**REGRA 12 — Estrutura óssea é sagrada**
O único erro que destrói aging cinematográfico é mudar a estrutura óssea (formato do crânio, espaçamento dos olhos, arco zigomático). Envelhecimento correto muda apenas pele, cabelo e gordura facial.

**REGRA 13 — Corpo envelhece junto com o rosto**
O erro de Hollywood em The Irishman: rosto jovem em corpo de 70 anos. Em AI, isso significa incluir postura, linguagem corporal e energia que correspondam à idade. "Youthful energy, inexperienced eyes" vs "wise expression, life-hardened gaze".

**REGRA 14 — Aging é contextual, não apenas físico**
Integre o envelhecimento físico com vestuário da época, cortes de cabelo e marcadores culturais. Um personagem envelhecido com roupa contemporânea em cena dos anos 1960 quebra completamente a credibilidade.

**REGRA 15 — Anchor phrase em TODOS os estágios**
A mesma anchor phrase do personagem jovem vai em todos os prompts de aging, seguida dos descritores específicos da faixa etária. A âncora garante que é o mesmo personagem — os descritores de idade garantem que parece mais velho.

---

## BLOCO C — ENVIRONMENT & WORLD (Regras 16-22)

**REGRA 16 — Visual Bible antes de qualquer geração**
Crie o documento de paleta, materiais, regras de iluminação e exemplos aprovados ANTES da primeira geração de produção. A maioria descarta 50% das gerações por não ter feito isso.

**REGRA 17 — Função gera forma**
"Robô de inspeção para túneis alagados" sugere automaticamente: juntas vedadas, baixo perfil, lanternas potentes, desgaste por umidade. O propósito cria o visual — não o contrário.

**REGRA 18 — Superfícies perfeitas destroem credibilidade**
Sci-fi pristine parece render de marketing, não mundo real. Um ou dois sinais de uso (micro-scratches, faded markings, improvised repair) transformam decoração em mundo habitado. Não exagere — cobrir tudo de sujeira é o clichê oposto.

**REGRA 19 — Uma lógica visual dominante por mundo**
Utopia pristina + wasteland + megacity neon + colônia rústica não podem coexistir como ideias iguais. Escolha UMA lógica social dominante e deixe as outras existirem em relação a ela.

**REGRA 20 — 80% do prompt é fixo, 20% varia**
Mude apenas um elemento por iteração para aprender o que funciona. Quem muda o prompt inteiro a cada tentativa nunca descobre o que fez o último resultado funcionar.

**REGRA 21 — Iluminação é narrativa, não efeito**
Documente as REGRAS de iluminação de cada ambiente, não apenas a estética. "Neon exterior frio + interior quente = tensão entre fachada e humanidade" é uma regra narrativa. "Parece cyberpunk" não é.

**REGRA 22 — Gere atmosfera separada do personagem**
Névoa + personagem + cena em um único prompt reduz controle. Profissionais geram: (1) cena base, (2) névoa/partículas em fundo preto, (3) composição em post. Isso permite ajustar a atmosfera sem regenerar a cena.

---

## BLOCO D — PROMPT MASTERY (Regras 23-31)

**REGRA 23 — Tipo de plano primeiro, sempre**
"Medium close-up" ou "extreme wide" deve ser o primeiro elemento de qualquer prompt de vídeo ou imagem. Sem isso, o AI escolhe um plano arbitrário que pode não servir à narrativa.

**REGRA 24 — Especificidade de iluminação separa amador de profissional**
"Dramatic lighting" é genérico. "Single hard light source from top-left at 45°, warm amber 2800K, fills 70% shadow on right side" é cinematografia. A fonte de luz, cor e direção são o que separa uma imagem viva de uma imagem morta.

**REGRA 25 — Não use "hyper realistic" para fotorrealismo**
Em Midjourney especialmente, o termo aciona associações com renders artificiais. Use "photorealistic", "RAW photo", ou "shot on [camera brand]" para resultados fotográficos autênticos.

**REGRA 26 — Negative prompts customizados, não universais**
Um negative prompt para retratos é diferente de um para paisagens. Personalize: retrato = foque em pele/anatomia/rosto; paisagem = foque em textura/perspectiva; ação = foque em blur/deformação.

**REGRA 27 — Máximo 150 palavras no negative prompt**
Acima de 150 palavras, você entra em rendimentos decrescentes e possíveis conflitos entre termos. Priorize os mais impactantes para o seu tipo de cena.

**REGRA 28 — Negative prompt não pode contradizer o positive**
Se quer "soft dreamy portrait" e coloca "soft focus, hazy" no negativo — você está cancelando o efeito desejado. Revise sempre os dois juntos.

**REGRA 29 — Máximo 2-3 técnicas de composição por imagem**
Tentar usar Golden Ratio + Leading Lines + Framing within Frame + Chiaroscuro ao mesmo tempo cria caos visual. Escolha as 2-3 técnicas que servem à história daquela imagem.

**REGRA 30 — Movimento de câmera específico, nunca genérico**
"The camera moves" = resultado aleatório. "Slow dolly-in maintaining eye level, camera physically advances 50% of original distance over 5 seconds" = cinematografia controlada.

**REGRA 31 — Referências culturais específicas valem mais que adjetivos**
"Blade Runner meets contemporary Tokyo" > "futuristic city with neon lights". "Roger Deakins cinematography" > "beautiful cinematic lighting". Uma boa referência cultural vale cinco adjetivos.

---

## BLOCO E — VFX & COMPOSITING (Regras 32-36)

**REGRA 32 — Efeitos luminosos sempre em fundo preto puro**
Hologramas, partículas, glow, fog, laser — sempre gerados em pure black background para compositing com Screen/Add blending. Nunca inseridos diretamente na cena final em geração única.

**REGRA 33 — Direção de névoa: "outward from background to foreground", nunca "toward camera"**
Prompts de névoa/fumaça com "toward camera/viewer/screen" têm baixa aderência nos modelos atuais. Use "flows from distant plane to close plane" ou "outward from background" para resultados consistentes.

**REGRA 34 — Color matching no compositing é obrigatório**
O maior erro no compositing é quando o elemento AI gerado tem temperatura de cor diferente do footage. Sempre faça color correction do elemento para combinar com a cena antes de compositar. Isso é o que quebra a ilusão.

**REGRA 35 — Não confie no AI para sombras interativas**
AI gera o elemento, mas projetar sombras corretas do personagem no ambiente e reflexos interativos em superfícies ainda requer After Effects / Nuke. O olho humano detecta sombras "impossíveis" instintivamente.

**REGRA 36 — Não regenere do zero para ajustes pequenos**
Use ferramentas com edição não-destrutiva: Luma Uni-1 edita elementos específicos preservando o aprovado, Runway permite edits locais. Runway Edit Studio (Aleph) muda fundo, roupa, produto e iluminação sem regenerar a cena inteira.

---

## BLOCO F — ÁUDIO PROFISSIONAL (Regras 37-40)

**REGRA 37 — Gere áudio primeiro, vídeo segundo**
Produza voiceover e trilha musical antes de qualquer geração de vídeo. Identifique beat drops e momentos de impacto no áudio e use esses timestamps como guia nos prompts de vídeo para alinhar cortes e movimentos de câmera.

**REGRA 38 — Música a -18dB a -20dB sob voiceover**
A hierarquia sonora é lei. Voiceover no topo, música serve a ele. Volumes similares tornam a narração ininteligível.

**REGRA 39 — Nunca Udio para produção comercial após outubro 2025**
Acordo com Universal Music Group proibiu todos os downloads. Qualquer música gerada após essa data fica presa na plataforma. Substitua por Suno V6 Pro.

**REGRA 40 — Stems separados são obrigatórios na entrega**
Entregar apenas mix final sem stems (música isolada, voz isolada, SFX isolados, ambiência isolada) impede correções futuras e re-versioning. Sempre guardar o projeto com stems.

---

## BLOCO G — COLOR & PIPELINE (Regras 41-44)

**REGRA 41 — Sempre trabalhe em scene-referred (LOG), nunca display-referred**
Grade em Rec.709 desde o início limita a imagem cedo, perde detalhes de highlight e shadow, e o grade não translada bem para outros destinos. DaVinci Wide Gamut/Intermediate como espaço de trabalho, Rec.709 apenas no output.

**REGRA 42 — CSTs manuais, não automáticos, para controle cirúrgico**
Os menus de Timeline e Output Color Space no DaVinci YRGB mode controlam apenas metadata tags, não o color management real. Crie CSTs manualmente nos nós para cada clip.

**REGRA 43 — LUTs têm especificações de input/output**
Um LUT criado para ARRI LogC3 aplicado em footage Rec.709 produzirá resultado destruído. Sempre confirme o espaço de cor de input/output de cada LUT antes de aplicar.

**REGRA 44 — Log Wheels para ajustes sutis, Color Wheels para correções grandes**
Color Wheels afetam faixas amplas da curva. Log Wheels afetam faixas estreitas específicas. Usar Color Wheels para ajustes finos resulta em grades descalibrados.

---

## BLOCO H — PRODUÇÃO & WORKFLOW (Regras 45-50)

**REGRA 45 — Pipelines híbridos são obrigatórios, nunca uma ferramenta única**
Quem usa só Kling perde qualidade cinematográfica do Runway. Quem usa só Runway perde consistência nativa de personagem do Kling. A comunidade profissional é unânime: rascunhe em Kling, finalize em Runway, upscale com Topaz.

**REGRA 46 — Teste de consistência antes de produção completa**
Gere 5-10 cenas teste ANTES de comprometer o orçamento total de créditos. Descubra as limitações da ferramenta escolhida para seu personagem específico antes de começar.

**REGRA 47 — Verifique licenças antes de qualquer produção comercial**
Suno free = apenas pessoal. Midjourney free = sem comercial. ElevenLabs Starter = proíbe streaming. Toda ferramenta tem restrições de licença por plano. Verifique sempre os termos antes de usar em comercial.

**REGRA 48 — Upscale é obrigatório antes da entrega broadcast**
A maioria das ferramentas AI gera em 720p nativo. Para broadcast e digital de alta qualidade, Topaz Video AI Astra para 4K é essencial. A falta de upscale é percebida imediatamente por diretores de arte.

**REGRA 49 — Emoção primeiro, continuidade por último**
Regra dos Seis de Walter Murch: Emoção (51%) > História (23%) > Ritmo (10%) > Eye-trace (7%) > Plano 2D (5%) > Espaço 3D (4%). Se precisar escolher entre um corte emocionalmente perfeito que quebra continuidade e um continuidade perfeita sem emoção, escolha sempre a emoção.

**REGRA 50 — A Bible é o projeto**
O documento de produção — Character Bible, Environment Bible, Costume Bible, Color Bible — não é documentação do que foi feito. É o documento que GUIA o que será feito. Quanto mais completa e específica a Bible antes de começar, mais o AI trabalha como um departamento inteiro em vez de um gerador aleatório. Uma Bible de 25 páginas transforma um projeto de 3 semanas em um projeto de 3 dias.

---

---

## APÊNDICE — REFERÊNCIA RÁPIDA

### Estrutura de Prompt de Imagem (9 elementos)
`[Câmera] + [Lente/AR] + [Fonte de luz] + [Paleta HEX] + [Composição] + [Sujeito+Anchor] + [Ação] + [Atmosfera+Cenário] + [Referência estética]`

### Estrutura de Prompt de Vídeo (7 elementos)
`[Movimento câmera] + [Sujeito+Identidade] + [Ação simples] + [Ambiente] + [Iluminação] + [Estilo] + [Tom+Técnico]`

### Estrutura de Prompt de Música (7 elementos)
`[Gênero] + [Subgênero] + [Instrumentos] + [Mood] + [BPM] + [Duração] + [Vocal/Instrumental]`

### Workflow Resumido
```
Character Sheets (Midjourney --cref)
    → Storyboard (Storyboarder.ai)
    → Vídeo personagens (Kling 3.0 Elements)
    → Vídeo hero shots (Runway Gen-4.5 ou Veo 3.1)
    → Áudio (ElevenLabs voz + Suno V6 músic)
    → VFX em fundo preto (Kling via ComfyUI)
    → Composite (After Effects / Fusion)
    → Upscale (Topaz Astra)
    → Color Grade (DaVinci Resolve)
    → Export com stems separados
```

### Ferramentas Essenciais por Categoria
- **Vídeo principal:** Kling 3.0 (personagens) + Runway Gen-4.5 (qualidade)
- **Imagem:** Midjourney V7 (character sheets) + Flux Pro (cenários fotorrealistas)
- **Voz:** ElevenLabs v3
- **Música:** Suno V6 Pro
- **SFX:** ElevenLabs Sound Effects
- **Compositing:** Adobe After Effects / DaVinci Fusion
- **Color Grade:** DaVinci Resolve Studio
- **Upscale:** Topaz Video AI Astra
- **NUNCA para comercial:** Udio (downloads desabilitados out/2025)

---

*CineForge Master Bible v1.0 — Outubro 2026*
*Baseada em pesquisa extensiva de 12 domínios de produção cinematográfica AI, consenso de comunidades profissionais (Reddit, Discord, YouTube, LinkedIn), benchmarks independentes e práticas validadas pela indústria Hollywood.*