#!/usr/bin/env bash
# =============================================================================
# ONDE RODAR: no terminal web do Pod RunPod temporário, com o Network Volume
# montado em /workspace (em Serverless o mesmo volume aparece em /runpod-volume).
#
# O que faz (uma vez por variante):
#   1. baixa do Hugging Face, em revisões FIXAS, só os arquivos que o diffusers usa
#      (sem assets/, examples/ nem README);
#   2. confere tamanho e hash de cada arquivo contra o manifesto abaixo
#      (sha256 dos arquivos LFS; hash git dos arquivos pequenos);
#   3. converte os shards dos transformers de F32 para BF16 com convert_to_bf16.py,
#      mantendo em F32 os módulos que o diffusers mantém em F32 ao carregar
#      (resultado numérico idêntico ao do arquivo original; metade do espaço);
#   4. grava SOURCES.txt e o marcador .cineforge_ready.
#
# Variáveis:
#   VARIANT=ti2v-5b (padrão, ~34 GB baixados -> ~24,2 GB no volume)
#   VARIANT=a14b    (~126 GB baixados -> ~69,1 GB no volume)
#   VARIANT=all     (as duas; ~93,3 GB no volume)
#   VOL=/workspace  TMP_DL=/root/wan22-dl (disco do container; precisa de ~6 GB livres)
#   DRY_RUN=1       só mostra o plano
#   ONLY='glob1,glob2' baixa só os caminhos que casam (teste/diagnóstico; não grava o marcador)
#
# Nada aqui executa código de repositório: só baixa pesos e roda convert_to_bf16.py.
# Licença dos dois repositórios: Apache-2.0.
# =============================================================================
set -Eeuo pipefail

VOL="${VOL:-/workspace}"
VARIANT="${VARIANT:-ti2v-5b}"
TMP_DL="${TMP_DL:-/root/wan22-dl}"
DRY_RUN="${DRY_RUN:-0}"
ONLY="${ONLY:-}"
DEST_ROOT="$VOL/wan22"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONVERT="$HERE/convert_to_bf16.py"
KEEP_FP32="time_embedder,scale_shift_table,norm1,norm2,norm3"

A14B_REPO="Wan-AI/Wan2.2-T2V-A14B-Diffusers"
A14B_REV="5be7df9619b54f4e2667b2755bc6a756675b5cd7"
A14B_DIR="Wan2.2-T2V-A14B-Diffusers"
TI2V_REPO="Wan-AI/Wan2.2-TI2V-5B-Diffusers"
TI2V_REV="b8fff7315c768468a5333511427288870b2e9635"
TI2V_DIR="Wan2.2-TI2V-5B-Diffusers"

# variante <TAB> caminho <TAB> bytes <TAB> tipo_hash <TAB> hash <TAB> ação (copy|bf16)
read -r -d '' MANIFEST <<'TSV' || true
ti2v-5b	model_index.json	499	gitsha1	fe52bfbdc8e5bbc8a6a607dd301f6e1ab0889cd1	copy
ti2v-5b	scheduler/scheduler_config.json	820	gitsha1	950d26faea717c8902ee197982026cb9c1b6463e	copy
ti2v-5b	text_encoder/config.json	855	gitsha1	ab4a73bce055c6e32e66133032dcb3adfb26ee8d	copy
ti2v-5b	text_encoder/model-00001-of-00003.safetensors	4935812536	sha256	a8e861969c7433e707cc5a74065d795d36cca07ec96eb6763eb4083df7248f58	copy
ti2v-5b	text_encoder/model-00002-of-00003.safetensors	4983103192	sha256	d57d948ece4837d850b7a859a4415121d57cacf8b9ee1d4db200c67f592902d7	copy
ti2v-5b	text_encoder/model-00003-of-00003.safetensors	1442935480	sha256	0da9ee284e21d1406df708788db1d502d95d75f69faa25cd26151bf8829b7c5f	copy
ti2v-5b	text_encoder/model.safetensors.index.json	22476	gitsha1	f3d3d4da90eb33e14c92d88ea346370fa3c0b5b2	copy
ti2v-5b	tokenizer/special_tokens_map.json	7079	gitsha1	2ed25bf989a28d20b5d4b5822fbc24666d12a6f7	copy
ti2v-5b	tokenizer/spiece.model	4548313	sha256	e3909a67b780650b35cf529ac782ad2b6b26e6d1f849d3fbb6a872905f452458	copy
ti2v-5b	tokenizer/tokenizer.json	16837459	sha256	20a46ac256746594ed7e1e3ef733b83fbc5a6f0922aa7480eda961743de080ef	copy
ti2v-5b	tokenizer/tokenizer_config.json	61758	gitsha1	09d434f9457238f697f4c208aab47f58caa15bfe	copy
ti2v-5b	transformer/config.json	495	gitsha1	8180887e8ed86e4fd842824fb15fcabf43d19512	copy
ti2v-5b	transformer/diffusion_pytorch_model-00001-of-00005.safetensors	4978254344	sha256	511bec832a201caa410d09c5ce7dbbf8ad2708c345d82038f684fc74cce982be	bf16
ti2v-5b	transformer/diffusion_pytorch_model-00002-of-00005.safetensors	4846784976	sha256	7c42724912b1911429125dc50c0e9a49ccbada5a601b657d4ed2e15e7597c193	bf16
ti2v-5b	transformer/diffusion_pytorch_model-00003-of-00005.safetensors	4972658392	sha256	e9c3d0c76de786566382f8258101fea973ae37681c6e9fe0e5fe1fb93b806424	bf16
ti2v-5b	transformer/diffusion_pytorch_model-00004-of-00005.safetensors	4846785080	sha256	a331121771790939678db6f585553fd5184609f7d02593c699a4d241b0d834c5	bf16
ti2v-5b	transformer/diffusion_pytorch_model-00005-of-00005.safetensors	354751840	sha256	78b655685c47efdb2349f36826bb101264e9f212a16325d584aeb5f53c88e719	bf16
ti2v-5b	transformer/diffusion_pytorch_model.safetensors.index.json	73297	gitsha1	4ced518ff3eb023a0477eeab55f2a4d45d6fd43a	copy
ti2v-5b	vae/config.json	1701	gitsha1	29f65bc63e9daadb95e4c1a8344d162be4b7d533	copy
ti2v-5b	vae/diffusion_pytorch_model.safetensors	2818777808	sha256	62cd18f19438e35b32ac63020e2852f566e9b02f46b6cdbd87972a356e3c6f4b	copy
a14b	model_index.json	498	gitsha1	f622781c91d39ea85a7a2c4e9f3e3652e6a467d8	copy
a14b	scheduler/scheduler_config.json	820	gitsha1	b5c4eaa781a10db1471bba005afeb90ce0391df5	copy
a14b	text_encoder/config.json	855	gitsha1	ab4a73bce055c6e32e66133032dcb3adfb26ee8d	copy
a14b	text_encoder/model-00001-of-00003.safetensors	4935812536	sha256	a8e861969c7433e707cc5a74065d795d36cca07ec96eb6763eb4083df7248f58	copy
a14b	text_encoder/model-00002-of-00003.safetensors	4983103192	sha256	d57d948ece4837d850b7a859a4415121d57cacf8b9ee1d4db200c67f592902d7	copy
a14b	text_encoder/model-00003-of-00003.safetensors	1442935480	sha256	0da9ee284e21d1406df708788db1d502d95d75f69faa25cd26151bf8829b7c5f	copy
a14b	text_encoder/model.safetensors.index.json	22476	gitsha1	f3d3d4da90eb33e14c92d88ea346370fa3c0b5b2	copy
a14b	tokenizer/special_tokens_map.json	7079	gitsha1	2ed25bf989a28d20b5d4b5822fbc24666d12a6f7	copy
a14b	tokenizer/spiece.model	4548313	sha256	e3909a67b780650b35cf529ac782ad2b6b26e6d1f849d3fbb6a872905f452458	copy
a14b	tokenizer/tokenizer.json	16837459	sha256	20a46ac256746594ed7e1e3ef733b83fbc5a6f0922aa7480eda961743de080ef	copy
a14b	tokenizer/tokenizer_config.json	61758	gitsha1	09d434f9457238f697f4c208aab47f58caa15bfe	copy
a14b	transformer/config.json	495	gitsha1	7f44f6167861ec54586f0b9fd7a336de2c4726af	copy
a14b	transformer/diffusion_pytorch_model-00001-of-00012.safetensors	4863171808	sha256	299e6304544f2783896372fa919e755a8bb9ab8caf898ce08a678dae391e1179	bf16
a14b	transformer/diffusion_pytorch_model-00002-of-00012.safetensors	4919594456	sha256	4eab1c97044607b5cd4c7647dc84d2274214b361018bbfb37f54206521d16440	bf16
a14b	transformer/diffusion_pytorch_model-00003-of-00012.safetensors	4919465128	sha256	2404f3bbd9a23e19d831ac7f3c115806f46251e2d2d175080b0ad8cdbe95abf9	bf16
a14b	transformer/diffusion_pytorch_model-00004-of-00012.safetensors	4919594536	sha256	b18cf5d61c46273ba8d347279694b58a6bdc9e29d4e517724c358430c5daa71a	bf16
a14b	transformer/diffusion_pytorch_model-00005-of-00012.safetensors	4919465224	sha256	928c0d327b1f2634be2efc2d577cd3570a229ac5af28bcd49a7687ab84206765	bf16
a14b	transformer/diffusion_pytorch_model-00006-of-00012.safetensors	4919594552	sha256	0083cb21891978e4657b46491b406f008b15dfe5da82762e30b3c9810e2838de	bf16
a14b	transformer/diffusion_pytorch_model-00007-of-00012.safetensors	4919465224	sha256	53d13464c39397bea88a5e1ee4c5cee522c9f3e094e4e49b4f4d2f88ef20ccd5	bf16
a14b	transformer/diffusion_pytorch_model-00008-of-00012.safetensors	4919594552	sha256	55bb416621d2ab08ac17542f854b98775040bd46937d8a4358e5d975f9c54a55	bf16
a14b	transformer/diffusion_pytorch_model-00009-of-00012.safetensors	4919465224	sha256	147369a6e7ec0344214b6cbca628461ca67d1a5933798dbb5be8af75f64647b5	bf16
a14b	transformer/diffusion_pytorch_model-00010-of-00012.safetensors	4919594552	sha256	88dd8a815f6458daaea0554dea7a0693c74d22bd38f116a0b489754ce6743b35	bf16
a14b	transformer/diffusion_pytorch_model-00011-of-00012.safetensors	4919465224	sha256	e9f0719271fa6363a1eae653e8922b4f5083be18f7db650f0c112ca4a39bc3d4	bf16
a14b	transformer/diffusion_pytorch_model-00012-of-00012.safetensors	3095607280	sha256	79b5fe7a2de29c3fc2a8eb0833f9d8465b3a070a7ac32bb3cc4a2577b20509cd	bf16
a14b	transformer/diffusion_pytorch_model.safetensors.index.json	97307	gitsha1	b29530a9c245dbd4efd4b75d65fd34111690151b	copy
a14b	transformer_2/config.json	495	gitsha1	7f44f6167861ec54586f0b9fd7a336de2c4726af	copy
a14b	transformer_2/diffusion_pytorch_model-00001-of-00012.safetensors	4863171808	sha256	a9278e6e9c82d174e6c67b3c97d8b97fef30af51dcf59160f2fc241f6819f5dc	bf16
a14b	transformer_2/diffusion_pytorch_model-00002-of-00012.safetensors	4919594456	sha256	db9212d47d0c3ce8b0e96e2f4def48e16a55b6f044067e6eff2647098c16eaa8	bf16
a14b	transformer_2/diffusion_pytorch_model-00003-of-00012.safetensors	4919465128	sha256	4764464b6d2023e7f24f135d9703fca28cc437793879292cecf229e0f2dcd564	bf16
a14b	transformer_2/diffusion_pytorch_model-00004-of-00012.safetensors	4919594536	sha256	dad95c9d4a568a8222b42cee5d391df2fd0f7c22cea03d8f5f28c71a2070f348	bf16
a14b	transformer_2/diffusion_pytorch_model-00005-of-00012.safetensors	4919465224	sha256	f11242f8014d046bb65736a64a20bbb6f8efe566373628307bfd687c811fecc3	bf16
a14b	transformer_2/diffusion_pytorch_model-00006-of-00012.safetensors	4919594552	sha256	8581b91ab7ecab2bae7f607176119bd8b8ec65ce9f67915ba7a6d9e9a36d2571	bf16
a14b	transformer_2/diffusion_pytorch_model-00007-of-00012.safetensors	4919465224	sha256	fc658a5689cd15edfc24bf1396bcd9644237ebfa18c2309ece986c99d0c9b054	bf16
a14b	transformer_2/diffusion_pytorch_model-00008-of-00012.safetensors	4919594552	sha256	c1e13c829853f10bd31725b62dc6cfc632de5a168d2520022fa3958edad63334	bf16
a14b	transformer_2/diffusion_pytorch_model-00009-of-00012.safetensors	4919465224	sha256	60cf08760beac7129e9194ecba8ecf394e484b882987704e5b54a1170837f3ba	bf16
a14b	transformer_2/diffusion_pytorch_model-00010-of-00012.safetensors	4919594552	sha256	f63297e6ecbe7f67654b87f9a1abdd93f6b369c07c91fd8e2fc9df42bd01d6f2	bf16
a14b	transformer_2/diffusion_pytorch_model-00011-of-00012.safetensors	4919465224	sha256	11fdb612135d52ac770304261f5e1a846882b72a5e81be15970c051edf20b518	bf16
a14b	transformer_2/diffusion_pytorch_model-00012-of-00012.safetensors	3095607280	sha256	23dbf3244e8dd60ef4fb1867d75407f627c771e3d248e87fba57164b4cd91593	bf16
a14b	transformer_2/diffusion_pytorch_model.safetensors.index.json	97307	gitsha1	b29530a9c245dbd4efd4b75d65fd34111690151b	copy
a14b	vae/config.json	724	gitsha1	c190b2929391232ec2f6e493dfe93542927e74ea	copy
a14b	vae/diffusion_pytorch_model.safetensors	507591892	sha256	d6e524b3fffede1787a74e81b30976dce5400c4439ba64222168e607ed19e793	copy
TSV

log() { printf '\n[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }
die() { printf '\nERRO: %s\n' "$*" >&2; exit 1; }
gb() { awk -v b="$1" 'BEGIN { printf "%.1f", b / 1e9 }'; }
free_bytes() { df -B1 --output=avail "$1" | tail -1 | tr -d ' '; }

repo_of() { case "$1" in a14b) echo "$A14B_REPO" ;; ti2v-5b) echo "$TI2V_REPO" ;; esac; }
rev_of() { case "$1" in a14b) echo "$A14B_REV" ;; ti2v-5b) echo "$TI2V_REV" ;; esac; }
dir_of() { case "$1" in a14b) echo "$A14B_DIR" ;; ti2v-5b) echo "$TI2V_DIR" ;; esac; }
other_of() { case "$1" in a14b) echo "ti2v-5b" ;; ti2v-5b) echo "a14b" ;; esac; }

need_space() {  # need_space <dir> <bytes>
  mkdir -p "$1"
  local avail; avail=$(free_bytes "$1")
  [ "$avail" -ge "$2" ] || die "espaço insuficiente em $1: $(gb "$avail") GB livres, preciso de $(gb "$2") GB"
}

git_blob_sha1() {
  python3 - "$1" <<'PY'
import hashlib, sys
data = open(sys.argv[1], "rb").read()
print(hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest())
PY
}

hash_ok() {  # hash_ok <arquivo> <tamanho> <tipo> <hash>
  [ -f "$1" ] && [ "$(stat -c %s "$1")" = "$2" ] || return 1
  if [ "$3" = "sha256" ]; then
    echo "$4  $1" | sha256sum -c --quiet - >/dev/null 2>&1
  else
    [ "$(git_blob_sha1 "$1")" = "$4" ]
  fi
}

curl_resume() {  # curl_resume <url> <arquivo.part>  (10 tentativas, retoma de onde parou)
  local i
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -L --fail --silent --show-error -C - -o "$2" "$1"; then return 0; fi
    log "download interrompido (tentativa $i/10); retomando em 15 s"
    sleep 15
  done
  return 1
}

fetch_verified() {  # fetch_verified <url> <destino> <tamanho> <tipo> <hash>
  local url="$1" out="$2" size="$3" htype="$4" hash="$5"
  mkdir -p "$(dirname "$out")"
  if hash_ok "$out" "$size" "$htype" "$hash"; then
    return 0
  fi
  rm -f "$out"
  log "baixando $(basename "$out") ($(gb "$size") GB)"
  curl_resume "$url" "$out.part" || die "falha ao baixar $url"
  mv -f "$out.part" "$out"
  hash_ok "$out" "$size" "$htype" "$hash" || { rm -f "$out"; die "tamanho/hash não confere em $out"; }
}

converted_ok() {  # converted_ok <arquivo final> <sha256 da origem>
  local out="$1" src_sha="$2"
  [ -f "$out" ] && [ -f "$out.sha256" ] && [ -f "$out.src_sha256" ] || return 1
  [ "$(cat "$out.src_sha256")" = "$src_sha" ] || return 1
  (cd "$(dirname "$out")" && sha256sum -c --quiet "$(basename "$out").sha256" >/dev/null 2>&1)
}

update_index_total() {  # recalcula metadata.total_size do *.index.json após a conversão
  python3 - "$1" <<'PY'
import json, os, struct, sys
idx = sys.argv[1]
base = os.path.dirname(idx)
with open(idx) as fh:
    data = json.load(fh)
total = 0
for shard in sorted(set(data["weight_map"].values())):
    with open(os.path.join(base, shard), "rb") as fh:
        (n,) = struct.unpack("<Q", fh.read(8))
        header = json.loads(fh.read(n))
    total += sum(v["data_offsets"][1] - v["data_offsets"][0] for k, v in header.items() if k != "__metadata__")
data.setdefault("metadata", {})["total_size"] = total
tmp = idx + ".tmp"
with open(tmp, "w") as fh:
    json.dump(data, fh, indent=2)
os.replace(tmp, idx)
print(f"{os.path.relpath(idx, os.path.dirname(base))}: total_size={total}")
PY
}

selected() {  # selected <caminho>: verdadeiro se ONLY está vazio ou se um dos globs (vírgula) casa
  [ -z "$ONLY" ] && return 0
  local pats pat
  IFS=',' read -ra pats <<< "$ONLY"
  for pat in "${pats[@]}"; do
    # shellcheck disable=SC2254
    case "$1" in $pat) return 0 ;; esac
  done
  return 1
}

process_variant() {
  local v="$1"
  local repo rev dir dest
  repo=$(repo_of "$v"); rev=$(rev_of "$v"); dir=$(dir_of "$v")
  dest="$DEST_ROOT/$dir"
  local lines; lines=$(printf '%s\n' "$MANIFEST" | awk -F'\t' -v v="$v" '$1 == v')
  local dl_bytes=0 vol_bytes=0 n=0
  while IFS=$'\t' read -r _ path size _ _ action; do
    selected "$path" || continue
    n=$((n + 1)); dl_bytes=$((dl_bytes + size))
    if [ "$action" = "bf16" ]; then vol_bytes=$((vol_bytes + size / 2)); else vol_bytes=$((vol_bytes + size)); fi
  done <<< "$lines"
  log "$v: $repo @ $rev"
  log "$v: $n arquivos | download $(gb "$dl_bytes") GB | no volume ~$(gb "$vol_bytes") GB | destino $dest"
  if [ "$DRY_RUN" = "1" ]; then
    while IFS=$'\t' read -r _ path size _ _ action; do
      selected "$path" || continue
      printf '  %-6s %8s GB  %s\n' "$action" "$(gb "$size")" "$path"
    done <<< "$lines"
    return 0
  fi
  local have=0
  [ -d "$dest" ] && have=$(du -sb "$dest" | cut -f1)
  [ "$have" -lt "$vol_bytes" ] && need_space "$DEST_ROOT" $((vol_bytes - have + 1000000000))
  local other_dir; other_dir="$DEST_ROOT/$(dir_of "$(other_of "$v")")"

  while IFS=$'\t' read -r _ path size htype hash action; do
    selected "$path" || continue
    local out="$dest/$path" url="https://huggingface.co/$repo/resolve/$rev/$path"
    if [ "$action" = "copy" ]; then
      if ! hash_ok "$out" "$size" "$htype" "$hash" && hash_ok "$other_dir/$path" "$size" "$htype" "$hash"; then
        log "reaproveitando $path da outra variante (mesmo hash)"
        mkdir -p "$(dirname "$out")"
        cp -f "$other_dir/$path" "$out"
      fi
      fetch_verified "$url" "$out" "$size" "$htype" "$hash"
      continue
    fi
    # action = bf16: baixa o shard F32 no disco do container, confere e converte para o volume
    if converted_ok "$out" "$hash"; then
      log "já convertido: $path"
      continue
    fi
    need_space "$TMP_DL" $((size + 500000000))
    local tmp
    tmp="$TMP_DL/$v-$(basename "$path")"
    fetch_verified "$url" "$tmp" "$size" "$htype" "$hash"
    need_space "$(dirname "$out")" $((size / 2 + 200000000))
    log "convertendo $path para BF16 (mantendo em F32: $KEEP_FP32)"
    python3 "$CONVERT" --src "$tmp" --dst "$out" --expect-sha256 "$hash" --keep-fp32 "$KEEP_FP32"
    echo "$hash" > "$out.src_sha256"
    rm -f "$tmp"
  done <<< "$lines"

  if [ -n "$ONLY" ]; then
    log "$v: ONLY='$ONLY' — download parcial; marcador .cineforge_ready não gravado"
    return 0
  fi
  local comp
  for comp in transformer transformer_2; do
    if [ -f "$dest/$comp/diffusion_pytorch_model.safetensors.index.json" ]; then
      update_index_total "$dest/$comp/diffusion_pytorch_model.safetensors.index.json"
    fi
  done
  cat > "$dest/SOURCES.txt" <<EOF
Modelo: https://huggingface.co/$repo (licença Apache-2.0)
Revisão fixada: $rev
Transformers convertidos F32 -> BF16 (mantidos em F32: $KEEP_FP32) com convert_to_bf16.py
Gerado em: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
  printf 'revision=%s\nrepo=%s\ndate=%s\n' "$rev" "$repo" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$dest/.cineforge_ready"
  log "$v: pronto em $dest ($(du -sh "$dest" | cut -f1))"
}

# ---------------------------------------------------------------------------
case "$VARIANT" in ti2v-5b|a14b|all) ;; *) die "VARIANT deve ser ti2v-5b, a14b ou all" ;; esac
if [ "$DRY_RUN" != "1" ]; then
  [ -d "$VOL" ] || die "$VOL não existe: anexe o Network Volume ao Pod"
  [ -f "$CONVERT" ] || die "convert_to_bf16.py precisa estar na mesma pasta deste script"
  command -v curl >/dev/null || die "curl ausente no Pod"
  command -v sha256sum >/dev/null || die "sha256sum ausente no Pod"
  python3 -c "import numpy" 2>/dev/null || {
    log "instalando numpy (dependência do conversor)"
    python3 -m pip install --no-cache-dir "numpy==1.26.4"
  }
  log "volume: $VOL | livre: $(gb "$(free_bytes "$VOL")") GB"
fi

if [ "$VARIANT" = "all" ]; then
  process_variant ti2v-5b
  process_variant a14b
else
  process_variant "$VARIANT"
fi
rmdir "$TMP_DL" 2>/dev/null || true
if [ "$DRY_RUN" != "1" ]; then
  log "concluído. Uso do volume:"
  du -sh "$DEST_ROOT"/* 2>/dev/null || true
  log "PRÓXIMO PASSO: encerre (Terminate) este Pod para parar a cobrança. O volume continua."
fi
