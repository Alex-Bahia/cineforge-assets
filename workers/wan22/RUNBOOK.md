# RUNBOOK — Worker Wan 2.2 no RunPod Serverless (CineForge AI)

Este pacote vai para `cineforge-assets/workers/wan22/` e cria o endpoint Serverless que
recebe o payload do `hermes_api.py /gerar-cena` (o MESMO contrato do worker HoloCine) e
devolve o MP4 em `output.video_b64`.

```
VPS (hermes_api /gerar-cena) ──/run──▶ Endpoint Serverless (imagem construída do GitHub)
                              ◀─/status─ worker lê os pesos do Network Volume (/runpod-volume/wan22)
```

Arquivos: `handler.py` (worker), `Dockerfile`, `requirements.txt` + `constraints.txt`
(versões fixas), `download_models.sh` + `convert_to_bf16.py` (preenchem o volume),
`test_input.json`, `tests/` (47 testes sem GPU + 7 de integração com o diffusers real em CPU).

---

## 0. Leia antes — o que mudou em relação ao HoloCine

1. **Licença comercial liberada.** Os dois modelos são **Apache-2.0** no Hugging Face
   (`Wan-AI/Wan2.2-T2V-A14B-Diffusers` e `Wan-AI/Wan2.2-TI2V-5B-Diffusers`), e o model card
   diz que os autores não reivindicam direitos sobre o conteúdo gerado. Continua valendo a
   regra da casa: só personagens e marcas originais, sem semelhança com pessoas reais.
2. **Duas variantes, escolhidas pela variável `MODEL_VARIANT` do endpoint:**

   | Variante | Uso | GPU | Padrões oficiais | Volume |
   |---|---|---|---|---|
   | `ti2v-5b` | 1º teste barato | 48 GB (A40/A6000) | 704×1280, 24 fps, 121 frames (5 s), 50 passos, guidance 5,0, shift 5,0 | 24,2 GB |
   | `a14b` | produção | 80 GB (H100/A100) | 480×832 ou 720×1280, 16 fps, 81 frames (5 s), 40 passos, guidance 4,0/3,0, shift 12,0 | 69,1 GB |

3. **Multi-shot = um plano por chamada.** Cada plano é gerado com
   `prompt = global caption + caption do plano` (a frase "This scene contains N shots." é
   removida, porque cada chamada gera um plano só). O trecho de cada plano é arredondado para
   cima até 4k+1 frames, gerado com seed próprio e aparado; os planos viram cortes secos num
   único H.264. **Limite por plano:** 81 frames no A14B e 121 no 5B (a duração de treino). O
   padrão antigo do HoloCine (241 frames) agora precisa de 3+ planos no A14B; o worker recusa
   antes de gastar GPU e diz o que ajustar.
4. **A consistência de personagem entre planos vem do texto.** Não há atenção entre planos
   como no HoloCine: descreva o personagem na global caption (roupa, cabelo, cores) e repita
   os traços principais na caption de cada plano. Continuidade por imagem (último frame →
   image-to-video) fica como evolução, ver §12.
5. **Shift do scheduler:** o código oficial do Wan 2.2 usa `sample_shift = 12.0` no T2V-A14B,
   mas o `scheduler_config.json` do repositório -Diffusers vem com `flow_shift = 3.0`. O worker
   segue o oficial (12,0); dá para mudar por job (`flow_shift`) ou no endpoint (`WAN_FLOW_SHIFT`).
6. **Pesos convertidos para BF16 no volume.** Os transformers vêm em F32 no Hugging Face
   (57,15 GB por expert no A14B). O `download_models.sh` converte para BF16 mantendo em F32 os
   módulos que o diffusers mantém em F32 — o resultado é bit a bit igual a carregar o original
   (testado), com metade do espaço e do tempo de leitura no cold start.

---

## 1. Decisões pendentes — tudo que custa dinheiro precisa do seu OK

Saldo na conta: **US$ 20,00**. Ordem sugerida (valores são **estimativas**, ver §10):

| # | Ação | Custo | Quando cobra |
|---|------|-------|--------------|
| D1 | Network Volume **30 GB** Standard (só o 5B) | US$ 0,07/GB/mês → **US$ 2,10/mês** | enquanto existir |
| D2 | Pod temporário para baixar o 5B (~20–40 min) | preço do Pod escolhido (estimativa ≤ US$ 0,50) | até o **Terminate** |
| D3 | Endpoint `wan22-5b` (Active 0, Max 1) | US$ 0 parado | só com worker rodando |
| D4 | 1º teste 5B: 2 planos, 121 frames, 704×1280 | **~US$ 0,15–0,35** (com cold start) | por segundo de GPU |
| D5 | Aumentar o volume para **100 GB** (5B + A14B) | **US$ 7,00/mês** | enquanto existir |
| D6 | Pod para baixar e converter o A14B (~45–90 min) | estimativa ≤ US$ 1,50 | até o **Terminate** |
| D7 | Endpoint `wan22-a14b` + teste 480P 81 frames | **~US$ 0,60–1,20** | por segundo de GPU |

Total D1–D7 na primeira semana ≈ **US$ 4–6** + o volume. Antes de começar, confira em
**Serverless** que nenhum endpoint antigo (wan21-video-gen, comfyui-flux-schnell,
nemotron-70b-instruct) está com **Active workers > 0** — worker ativo cobra 24 h por dia.

O volume só cresce (não diminui) e prende os endpoints ao data center dele.

---

## 2. Colocar o worker no repositório

**No terminal do Mac (alexandremenezes@...)** — ajuste a origem se o pacote estiver em outra pasta:

```bash
cd ~/cineforge-assets
mkdir -p workers/wan22
# copie para workers/wan22/ os arquivos deste pacote: handler.py, Dockerfile, requirements.txt,
# constraints.txt, convert_to_bf16.py, download_models.sh, test_input.json, tests/, RUNBOOK.md
git add workers/wan22
git commit -m "worker Wan 2.2 (diffusers) para RunPod Serverless"
git push
```

Opcional, se o repositório tiver mídias pesadas: crie `~/cineforge-assets/.dockerignore` com as
duas linhas `*` e `!workers/wan22` para o build não enviar o resto do repo.

Nenhum código de terceiros é clonado: o Wan entra pelo `diffusers==0.36.0` do PyPI, com
versões fixadas em `requirements.txt`/`constraints.txt`, e a imagem roda com `HF_HUB_OFFLINE=1`.

---

## 3. Conectar o GitHub ao RunPod (sem custo)

No navegador: **Settings → Connections → GitHub → Connect** → **Only select repositories →
cineforge-assets**. Limites do build pelo GitHub (docs.runpod.io): `docker build` ≤ 30 min,
processo total ≤ 160 min, imagem ≤ 80 GB, sem GPU no build. Esta imagem (~9 GB, só rodas
pré-compiladas) cabe. **Atualizar o worker exige criar uma Release no GitHub** — push sozinho
não reconstrói.

---

## 4. Criar o Network Volume (D1 — US$ 2,10/mês)

No navegador: **Storage → Create volume**

- Tipo **Standard**; Nome `wan22-models`; Tamanho **30 GB** (aumenta para 100 GB no §9).
- Data center: escolha um que mostre disponibilidade de **48 GB (A40/A6000)** e também de
  **80 GB (H100/A100)** — o volume prende os dois endpoints a esse data center. É a escolha
  mais importante do processo (o console já avisou oferta baixa de 80 GB no data center atual).

---

## 5. Baixar o 5B com um Pod temporário (D2)

No navegador: **Pods → Deploy** com o volume `wan22-models` anexado (Secure Cloud), a opção
mais barata disponível (o script não usa GPU), template **Runpod PyTorch** (já tem python3 e
numpy), disco do container padrão (o shard F32 temporário ocupa no máximo ~5 GB).

Envie `download_models.sh` e `convert_to_bf16.py` para `/workspace` pelo **JupyterLab** do Pod
(Connect → Jupyter Lab → arrastar os arquivos).

**No terminal web do Pod RunPod** — ver o plano sem baixar nada:

```bash
cd /workspace && DRY_RUN=1 VARIANT=ti2v-5b bash download_models.sh
```

**No terminal web do Pod RunPod** — baixar, conferir e converter (~34 GB baixados → 24,2 GB no volume):

```bash
cd /workspace && VARIANT=ti2v-5b bash download_models.sh 2>&1 | tee /workspace/download-5b.log
```

O script confere tamanho e hash de cada arquivo contra o manifesto fixado (revisão
`b8fff7315c768468a5333511427288870b2e9635`), retoma downloads interrompidos, pode ser rodado de
novo sem baixar o que já está certo e termina gravando `SOURCES.txt` e `.cineforge_ready`.

No navegador: **Pods → o Pod → Terminate** (Stop continua cobrando disco). O volume fica.

---

## 6. Endpoint de teste `wan22-5b` (D3 — só cobra quando roda)

No navegador: **Serverless → New Endpoint → Import Git Repository → cineforge-assets**

- Branch `main`; **Dockerfile Path `workers/wan22/Dockerfile`**
- Endpoint Name `wan22-5b`; Type **Queue**
- GPU: **48 GB** (A6000/A40, US$ 1,22/h) e, como reserva, **48 GB PRO** (L40S/6000 Ada,
  US$ 1,89/h). Não marque GPUs Blackwell (RTX 5090, B200): o PyTorch 2.6 cu124 não tem kernels
  para elas.
- Active workers **0** · Max workers **1** · GPUs/worker **1** · Idle timeout **60–120 s**
  (cada worker frio relê os pesos do volume — 24 GB no 5B, 69 GB no A14B, minutos de GPU paga;
  com 60–120 s, jobs em sequência reaproveitam o modelo carregado e o custo extra é no máximo
  esse tempo ocioso por lote. Para um teste isolado, 5 s economiza alguns centavos.)
- **Execution timeout 1800 s** · FlashBoot **ligado** · Network Volume **wan22-models**
- Variáveis de ambiente (nenhuma é segredo): **`MODEL_VARIANT=ti2v-5b`**. Opcional:
  `WAN_SAVE_OUTPUTS=1` guarda cópia em `/runpod-volume/wan22/outputs/<output_path>`.

Acompanhe **Builds** até **Completed** (~10–20 min) e anote o **Endpoint ID**.

O modelo carrega no primeiro job (não na inicialização), então o tempo de carga aparece em
`output.model_load_s`. Com 48 GB o worker escolhe sozinho o modo de memória (`WAN_OFFLOAD=auto`):
tudo residente na GPU e VAE em tiles (placas de 48 GiB reportam ~51 GB decimais; abaixo de 60 GB
o VAE decodifica em tiles; `WAN_VAE_TILING=0/1` força).

---

## 7. Chave de API e VPS

A chave `cineforge-hermes-vps` (Serverless Read/Write, sem REST e sem GraphQL) já foi criada.
O `RUNPOD_ENDPOINT_ID` da VPS recebe o ID do endpoint que você for usar, pelo procedimento do
`COMANDOS.md` da integração da VPS. O host do Serverless é `https://api.runpod.ai/v2/{ENDPOINT_ID}/...`.

Ajuste da VPS antes de clipes longos: o polling (`RUNPOD_POLL_TIMEOUT_S`) tem que ser maior que
o Execution timeout do endpoint e, ao desistir, chamar `/cancel/{job_id}`.

---

## 8. Primeiro teste (D4 — ~US$ 0,15–0,35)

**No terminal SSH da VPS (ubuntu@hermes-vps:~$)** — envia o teste (2 planos; no 5B, com
`num_frames` 121 = 5 s a 24 fps):

```bash
cd ~/cineforge-assets && set -a && . ./.env && set +a
JOB_ID=$(curl -sS -X POST "https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID/run" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
  --data-binary @- <<'JSON' | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("id") or d)'
{"input": {
  "global_caption": "A young woman in a yellow raincoat walks through a neon-lit rainy street at night, original character, cinematic style, shallow depth of field, wet pavement reflecting pink and cyan signs. This scene contains 2 shots.",
  "shot_captions": [
    "Wide shot: the woman in the yellow raincoat walks toward the camera, rain falling, neon reflections ripple on the wet pavement.",
    "Close-up: the woman's face under the yellow hood, water dripping from the brim, calm focused eyes, soft neon rim light."
  ],
  "num_frames": 121, "shot_cut_frames": [], "seed": 42,
  "output_path": "testes/wan22_5b_teste.mp4"
}}
JSON
)
echo "JOB_ID=$JOB_ID"
```

**No terminal SSH da VPS (ubuntu@hermes-vps:~$)** — acompanha o progresso e salva o MP4 em
`~/cineforge-assets/cenas/` (não imprime o base64):

```bash
cd ~/cineforge-assets && python3 - "$JOB_ID" <<'PY'
import base64, json, os, sys, time, urllib.request
job, ep, key = sys.argv[1], os.environ["RUNPOD_ENDPOINT_ID"], os.environ["RUNPOD_API_KEY"]
url = f"https://api.runpod.ai/v2/{ep}/status/{job}"
t0 = time.time()
while True:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    d = json.load(urllib.request.urlopen(req, timeout=30))
    st = d.get("status")
    extra = d.get("output") if st == "IN_PROGRESS" else ""
    print(f"{int(time.time() - t0):>5}s {st} {extra or ''}", flush=True)
    if st in ("COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"):
        break
    time.sleep(15)
out = d.get("output") if isinstance(d.get("output"), dict) else {}
if st == "COMPLETED" and "video_b64" in out:
    os.makedirs("cenas", exist_ok=True)
    path = os.path.join("cenas", out.get("file_name", "wan22.mp4"))
    with open(path, "wb") as fh:
        fh.write(base64.b64decode(out.pop("video_b64")))
    print("salvo em", os.path.abspath(path))
print(json.dumps(out, indent=2, ensure_ascii=False)[:4000])
if st != "COMPLETED":
    print("erro:", d.get("error") or out.get("error"))
PY
```

**No terminal SSH da VPS (ubuntu@hermes-vps:~$)** — para cancelar um job (e a cobrança):

```bash
cd ~/cineforge-assets && set -a && . ./.env && set +a
curl -sS -X POST "https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID/cancel/$JOB_ID" -H "Authorization: Bearer $RUNPOD_API_KEY"
```

Me mande o JSON final (sem o vídeo): `model_load_s`, `text_encode_s`, `generation_s` e
`shots[].generation_s` são os tempos reais que substituem as estimativas do §10 (e calibram
`WAN_REF_SECONDS`, §14).

---

## 9. Produção com o A14B (D5–D7)

1. No navegador: **Storage → wan22-models → aumentar para 100 GB** (US$ 7,00/mês).
2. Pod temporário com o volume (como no §5). **No terminal web do Pod RunPod:**

   ```bash
   cd /workspace && VARIANT=a14b bash download_models.sh 2>&1 | tee /workspace/download-a14b.log
   ```

   ~126 GB baixados → 69,1 GB no volume (o text encoder e o tokenizer, idênticos aos do 5B,
   são copiados do próprio volume em vez de baixados de novo). Depois: **Terminate** no Pod.
3. No navegador: **Serverless → New Endpoint** igual ao §6, com: nome `wan22-a14b`; GPU
   **80 GB PRO (H100)** e **80 GB (A100)** como reserva; **Execution timeout 3600 s**;
   **`MODEL_VARIANT=a14b`**. Com 80 GB o worker usa o modo `t5` (os dois experts residentes na
   GPU, o T5 sobe só para codificar os prompts; ~24 GB de RAM).
4. `RUNPOD_ENDPOINT_ID` da VPS passa a ser o ID do `wan22-a14b`; o `wan22-5b` fica para prévias.
5. Teste: mesmo comando do §8 com `"num_frames": 81` (480×832 é o padrão). Para 720P envie
   `"height": 720, "width": 1280` — só em GPU de 80 GB (o worker recusa em GPU menor).

---

## 10. Custos e tempos (estimativas com fontes)

Preços Serverless (runpod.io/pricing, 15/11/2026): **A40/A6000 48 GB US$ 1,22/h**,
**L40S/6000 Ada 48 GB US$ 1,89/h**, **A100 80 GB US$ 2,99/h**, **H100 PRO 80 GB US$ 5,89/h**.
Pods custam menos por hora (H100 a partir de US$ 1,99/h, A100 a partir de US$ 1,19/h na
mesma página): para produção em lote, um Pod com o mesmo volume sai mais barato que Serverless.
Volume: US$ 0,07/GB/mês (docs.runpod.io/storage/network-volumes).

Tempos de referência — tabela oficial "Computational Efficiency" do Wan 2.2 (1 GPU):
TI2V-5B 720P em RTX 4090: **534,7 s**; T2V-A14B 480P: **326,9 s em H100** e **785,7 s em
A100**; T2V-A14B 720P: **1041,5 s em H100** e **2735,7 s em A100**.

| Clipe (estimativa) | GPU | Geração | Custo por clipe |
|---|---|---|---|
| 5B, 121 frames 704×1280, 2 planos | A40/A6000 | ~6–12 min | **~US$ 0,12–0,25** + carga |
| A14B, 81 frames 480×832, 2 planos | H100 PRO | ~5–7 min | **~US$ 0,50–0,70** + carga |
| A14B, 81 frames 480×832, 2 planos | A100 80 GB | ~12–15 min | **~US$ 0,60–0,75** + carga |
| A14B, 81 frames 720×1280, 1 plano | H100 PRO | ~17–23 min | **~US$ 1,70–2,25** + carga |

"Carga" = ler os pesos do volume no cold start (24 GB no 5B, 69 GB no A14B; estimei 2–6 min,
não medido). Com o worker quente (FlashBoot/idle) a carga é zero. Dois planos de 41 frames
custam perto de um clipe de 81 (cada plano tem metade dos tokens). As estimativas assumem o
SDPA do PyTorch; a tabela oficial usa FlashAttention-3 em Hopper, então o H100 pode sair
10–30% mais lento que a referência. O primeiro teste mede os tempos reais.

---

## 11. Alternativa: build no Mac e Docker Hub

O Mac é Intel (x86-64): o build é nativo para `linux/amd64`, mas o upload de ~9 GB pela sua
internet é o gargalo. **No terminal do Mac (alexandremenezes@...)** (Docker Desktop aberto;
troque `SEU_USUARIO`):

```bash
cd ~/cineforge-assets
docker build --platform linux/amd64 -f workers/wan22/Dockerfile -t SEU_USUARIO/cineforge-wan22:0.1.0 .
docker push SEU_USUARIO/cineforge-wan22:0.1.0
```

Depois: **Serverless → New Endpoint → Import from Docker Registry** com
`docker.io/SEU_USUARIO/cineforge-wan22:0.1.0` e as mesmas configurações.

---

## 12. Evolução futura (não implementada): continuidade por imagem entre planos

Hoje cada plano parte do texto. Para continuidade visual mais forte (mesmo figurino e
cenário entre planos de mesmo ângulo), o próximo passo é usar o **último frame do plano k
como imagem inicial do plano k+1** (image-to-video). O 5B já faz isso com os mesmos pesos
(modo I2V do TI2V-5B); no A14B exigiria o `Wan2.2-I2V-A14B-Diffusers` (mais 2 experts de
57 GB em F32 → volume maior). Serve para continuação de ação, não para corte seco: o plano
seguinte começa exatamente onde o anterior terminou.

---

## 13. Testes locais (sem GPU, sem custo)

**No terminal do Mac (alexandremenezes@...)**:

```bash
cd ~/cineforge-assets/workers/wan22
python3 -m venv .venv && . .venv/bin/activate
pip install "numpy" "imageio==2.37.0" "imageio-ffmpeg==0.6.0" "pytest"
python -m pytest -q tests
deactivate
```

Esperado sem torch: 46 passam e 8 são pulados (7 de integração + 1 comparação com o torch).
São 47 testes de mock (contrato, 4k+1, cortes secos no frame certo dentro do MP4, seeds por plano,
padrões oficiais de cada variante, limite de 10 MB do `/run`, upload presigned, escolha de modo
de memória, checagem do volume, conversor BF16). Os 7 testes de integração (diffusers real com
modelos minúsculos em CPU) rodam se `torch`, `diffusers`, `transformers` e `accelerate` estiverem
instalados; sem eles são pulados. Neles, o vídeo do worker sai **pixel a pixel igual** ao do
`WanPipeline` padrão chamado com o prompt em texto.

---

## 14. Contrato do worker

Entrada (`input`), igual ao worker HoloCine: `global_caption`, `shot_captions` (1–13),
`num_frames` (total; padrão 81 no A14B e 121 no 5B; corrigido para 4t+1; 17–481),
`shot_cut_frames` (`[]` = automático; se vier, precisa ter planos−1 cortes), `negative_prompt`
(padrão: negativo oficial do Wan 2.2, em chinês), `seed` (0 = aleatório; o seed real volta na
saída; o plano 1 usa o seed, os demais usam seeds derivados e determinísticos), `output_path`,
`output_upload_url` (presigned PUT https), `return_base64`, `allow_prompt_truncation`.
Extras opcionais: `prompt` (modo bruto do HoloCine, convertido em planos), `num_inference_steps`
(4–60), `cfg_scale` (expert de ruído alto), `cfg_scale_2` (expert de ruído baixo, só A14B),
`flow_shift` (1–20), `fps`, `height`/`width` (múltiplos de 16 no A14B e de 32 no 5B), `crf`.

Validações que economizam GPU (respondem em segundos, sem carregar o modelo): frase
"This scene contains N shots." tem que bater com o número de planos; plano acima do limite de
frames ou abaixo de 8 frames; prompt de qualquer plano acima de 512 tokens do T5; tags
reservadas no texto; caminhos com `..`; 720P do A14B em GPU de menos de 80 GB (a GPU é consultada
antes de carregar o modelo); `cfg_scale=1` com `cfg_scale_2>1` (o diffusers ligaria o CFG só pelo
primeiro, e o segundo seria ignorado em silêncio); **job estimado acima do orçamento de GPU**:
frames × pixels^1,4 × passos, calibrado na tabela oficial (A14B: 786 s por 81 frames 480P/40 passos,
pior caso A100; 5B: 600 s por 121 frames 720P/50 passos), contra `WAN_MAX_GEN_SECONDS` (3000 s no
A14B e 1500 s no 5B, para caber nos Execution timeouts de 3600 s e 1800 s). Ex.: 481 frames no A14B
(6 planos × ~786 s ≈ 4700 s) é recusado. Depois do primeiro teste real, ajuste a referência à sua
GPU com `WAN_REF_SECONDS` (ex.: ~330 em H100) e o orçamento com `WAN_MAX_GEN_SECONDS`.

Saída: `video_b64`, `mime_type`, `file_name`, `frames`, `fps`, `seconds`, `width`, `height`,
`seed`, `shot_cut_frames`, `shots[]` (início, frames usados/gerados, seed, tokens, tempo de cada
plano), `num_inference_steps`, `cfg_scale`, `cfg_scale_2`, `flow_shift`, `vae_tiling`, `crf`,
`size_bytes`, `sha256`, `model_load_s`, `text_encode_s`, `generation_s`, `encode_s`, `elapsed_s`,
`worker{variant, repo, revision, offload, gpu, vram_gb, ram_gb, torch, diffusers}`, `warnings`.
Erro: `{"error": "..."}` (job FAILED). O MP4 inline respeita o limite de 10 MB do `/run`: se
passar, o worker recodifica com CRF +4 e +8 (no máximo 2 recodificações); se ainda assim não
couber, pede `output_upload_url`.

---

## 15. Riscos conhecidos

- **RAM do worker:** o RunPod não documenta a RAM dos workers Serverless. O modo `t5` do A14B
  precisa de ~24 GB; o modo `model` (A14B em GPU de 48 GB) precisa de ~80 GB e o worker
  recusa com mensagem clara se faltar. Por isso o A14B fica em GPU de 80 GB.
- **Oferta de GPU** no data center do volume: se faltar, os jobs ficam em fila. Mantenha duas
  opções de GPU por endpoint.
- **Cold start** de alguns minutos a cada worker frio (24 GB ou 69 GB lidos do volume).
- **Shift 12 vs 3** (§0.5): se os primeiros vídeos do A14B saírem com movimento estranho,
  teste `"flow_shift": 5` e `3` no mesmo seed antes de mudar o padrão.
- **Tempos e custos do §10 são estimativas** até o primeiro teste.
