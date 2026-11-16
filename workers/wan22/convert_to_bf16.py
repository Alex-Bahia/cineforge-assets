#!/usr/bin/env python3
"""
Converte um shard .safetensors F32 -> BF16 em streaming (pedaço a pedaço).

Por que: os transformers do Wan 2.2 (-Diffusers) estão em F32 no Hugging Face
(57,15 GB cada expert do A14B; 20 GB o do 5B). O worker carrega com
torch_dtype=bfloat16, então o volume pode guardar BF16 sem mudar o resultado:
metade do espaço, metade do tempo de leitura no cold start.

Resultado idêntico ao carregamento do F32 original, porque:
  * a conversão usa round-to-nearest-even, igual a torch.Tensor.to(torch.bfloat16);
  * os tensores dos módulos que o diffusers mantém em FP32 ao carregar
    (WanTransformer3DModel._keep_in_fp32_modules: time_embedder, scale_shift_table,
    norm1, norm2, norm3 — mesma regra de substring do diffusers) ficam em F32 aqui
    também: passe-os em --keep-fp32.

Uso (no terminal web do Pod RunPod):
  python3 convert_to_bf16.py --src shard_f32.safetensors --dst shard.safetensors \
      --keep-fp32 time_embedder,scale_shift_table,norm1,norm2,norm3 \
      [--expect-sha256 <sha256 do arquivo de origem>]
  curl -L URL | python3 convert_to_bf16.py --src - --dst saida.safetensors ...

Só depende de numpy. Nomes, formas e a ordem dos tensores são preservados, então o
arquivo *.safetensors.index.json do diffusers continua válido (só o total_size muda).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
from typing import BinaryIO, Dict, List, Sequence, Tuple

import numpy as np

DTYPE_SIZES = {"F64": 8, "F32": 4, "F16": 2, "BF16": 2, "I64": 8, "I32": 4, "I16": 2,
               "I8": 1, "U8": 1, "BOOL": 1, "U16": 2, "U32": 4, "U64": 8,
               "F8_E4M3": 1, "F8_E5M2": 1}
FLOAT_SRC = {"F32": "<f4", "F16": "<f2", "F64": "<f8"}
CHUNK_ELEMS = 16 * 1024 * 1024  # 64 MB de F32 por vez
MAX_HEADER = 100_000_000


class HashingReader:
    """Lê sequencialmente (arquivo ou stdin) e calcula o sha256 do que passou."""

    def __init__(self, fh: BinaryIO) -> None:
        self.fh = fh
        self.sha = hashlib.sha256()
        self.pos = 0

    def read_exact(self, n: int) -> bytes:
        parts = []
        remaining = n
        while remaining:
            chunk = self.fh.read(min(remaining, 8 * 1024 * 1024))
            if not chunk:
                raise EOFError(f"arquivo terminou antes do esperado (faltam {remaining} bytes)")
            parts.append(chunk)
            remaining -= len(chunk)
        data = b"".join(parts)
        self.sha.update(data)
        self.pos += n
        return data

    def drain(self) -> int:
        extra = 0
        while True:
            chunk = self.fh.read(8 * 1024 * 1024)
            if not chunk:
                return extra
            self.sha.update(chunk)
            extra += len(chunk)


def f32_to_bf16(raw: bytes) -> bytes:
    """F32 little-endian -> BF16 (RNE). NaN vira 0x7FC0, como no PyTorch."""
    a = np.frombuffer(raw, dtype="<u4")
    lsb = (a >> np.uint32(16)) & np.uint32(1)
    out = ((a + np.uint32(0x7FFF) + lsb) >> np.uint32(16)).astype("<u2")
    nan = ((a & np.uint32(0x7F800000)) == np.uint32(0x7F800000)) & ((a & np.uint32(0x007FFFFF)) != 0)
    if nan.any():
        out[nan] = np.uint16(0x7FC0)
    return out.tobytes()


def numel(shape: List[int]) -> int:
    n = 1
    for d in shape:
        n *= int(d)
    return n


def keep_original(name: str, keep_fp32: Sequence[str]) -> bool:
    """Mesma regra do diffusers (_keep_in_fp32_modules): substring no nome do tensor."""
    return any(pattern in name for pattern in keep_fp32)


def plan_layout(header: Dict, keep_fp32: Sequence[str] = ()) -> Tuple[Dict, List[Tuple[str, str, str, int, int]]]:
    meta = header.get("__metadata__")
    items = sorted(((k, v) for k, v in header.items() if k != "__metadata__"),
                   key=lambda kv: kv[1]["data_offsets"][0])
    new_header: Dict = {}
    plan = []
    offset = 0
    expected_begin = 0
    kept = 0
    for name, info in items:
        dtype, shape = info["dtype"], info["shape"]
        begin, end = info["data_offsets"]
        if dtype not in DTYPE_SIZES:
            raise ValueError(f"dtype não suportado em {name}: {dtype}")
        if begin != expected_begin:
            raise ValueError(f"buraco/sobreposição nos dados em {name} ({begin} != {expected_begin})")
        if end - begin != numel(shape) * DTYPE_SIZES[dtype]:
            raise ValueError(f"tamanho inconsistente em {name}")
        expected_begin = end
        if dtype in FLOAT_SRC and keep_original(name, keep_fp32):
            out_dtype = dtype
            kept += 1
        else:
            out_dtype = "BF16" if dtype in FLOAT_SRC else dtype
        out_size = numel(shape) * DTYPE_SIZES[out_dtype]
        new_header[name] = {"dtype": out_dtype, "shape": shape, "data_offsets": [offset, offset + out_size]}
        plan.append((name, dtype, out_dtype, begin, end))
        offset += out_size
    new_meta = dict(meta) if isinstance(meta, dict) else {}
    new_meta["cineforge_conversion"] = "f32->bf16 round-to-nearest-even"
    if keep_fp32:
        new_meta["cineforge_keep_fp32"] = ",".join(keep_fp32)
    new_header["__metadata__"] = {str(k): str(v) for k, v in new_meta.items()}
    return new_header, plan


def convert_stream(reader: HashingReader, dst: str, keep_fp32: Sequence[str] = ()) -> Dict[str, object]:
    (n,) = struct.unpack("<Q", reader.read_exact(8))
    if n <= 0 or n > MAX_HEADER:
        raise ValueError(f"cabeçalho safetensors inválido ({n} bytes)")
    header = json.loads(reader.read_exact(n))
    new_header, plan = plan_layout(header, keep_fp32)
    header_bytes = json.dumps(new_header, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    header_bytes += b" " * ((8 - len(header_bytes) % 8) % 8)

    tmp = dst + ".partial"
    out_sha = hashlib.sha256()
    converted = copied = 0
    with open(tmp, "wb") as out:
        def emit(data: bytes) -> None:
            out.write(data)
            out_sha.update(data)

        emit(struct.pack("<Q", len(header_bytes)))
        emit(header_bytes)
        for name, dtype, out_dtype, begin, end in plan:
            size = end - begin
            if out_dtype == dtype:
                left = size
                while left:
                    step = min(left, 64 * 1024 * 1024)
                    emit(reader.read_exact(step))
                    left -= step
                copied += 1
                continue
            item = DTYPE_SIZES[dtype]
            left_elems = size // item
            while left_elems:
                step = min(left_elems, CHUNK_ELEMS)
                raw = reader.read_exact(step * item)
                if dtype != "F32":
                    raw = np.frombuffer(raw, dtype=FLOAT_SRC[dtype]).astype("<f4").tobytes()
                emit(f32_to_bf16(raw))
                left_elems -= step
            converted += 1
        out.flush()
        os.fsync(out.fileno())
    return {"tmp": tmp, "out_sha256": out_sha.hexdigest(), "converted": converted,
            "copied": copied, "header_bytes": n}


def main(argv: List[str] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--src", required=True, help="arquivo .safetensors F32 ou '-' para stdin")
    ap.add_argument("--dst", required=True, help="arquivo .safetensors de saída (BF16 + F32 mantidos)")
    ap.add_argument("--expect-sha256", default="", help="sha256 esperado do arquivo de ORIGEM")
    ap.add_argument("--keep-fp32", default="",
                    help="substrings separadas por vírgula; tensores cujo nome contém uma delas ficam em F32")
    args = ap.parse_args(argv)
    keep_fp32 = tuple(p.strip() for p in args.keep_fp32.split(",") if p.strip())

    os.makedirs(os.path.dirname(os.path.abspath(args.dst)), exist_ok=True)
    fh = sys.stdin.buffer if args.src == "-" else open(args.src, "rb")
    try:
        reader = HashingReader(fh)
        info = convert_stream(reader, args.dst, keep_fp32)
        trailing = reader.drain()
    finally:
        if fh is not sys.stdin.buffer:
            fh.close()
    src_sha = reader.sha.hexdigest()
    if trailing:
        print(f"aviso: {trailing} bytes após o último tensor foram ignorados", file=sys.stderr)
    if args.expect_sha256 and src_sha != args.expect_sha256.lower():
        os.remove(info["tmp"])
        print(f"ERRO: sha256 da origem {src_sha} != esperado {args.expect_sha256}", file=sys.stderr)
        return 2
    os.replace(info["tmp"], args.dst)
    with open(args.dst + ".sha256", "w") as fh_sum:
        fh_sum.write(f"{info['out_sha256']}  {os.path.basename(args.dst)}\n")
    print(json.dumps({"dst": args.dst, "dst_sha256": info["out_sha256"], "src_sha256": src_sha,
                      "tensores_convertidos": info["converted"], "tensores_copiados": info["copied"],
                      "keep_fp32": list(keep_fp32), "bytes_saida": os.path.getsize(args.dst)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
