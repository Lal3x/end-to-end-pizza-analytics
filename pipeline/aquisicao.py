"""Aquisição íntegra e isolada, conforme specs/ingestao.md, regra 6.

Preserva respostas HTTP e só publica fontes após validar todos os hashes.
Não executa JavaScript remoto nem abre banco. A licença não é inferida pelo
download: dados ficam locais e a permissão é documentada separadamente.
"""

import gzip
import hashlib
import json
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from uuid import uuid4

from pipeline import db
from pipeline.fontes import BASE_URL, FONTES


def adquirir() -> Path:
    """Baixa a versão fixada ou confere fontes já existentes sem sobrescrever."""
    raiz = db.PASTA_RAW.parent
    destino = db.PASTA_RAW / "pizza_paradise"
    if destino.exists():
        for fonte in FONTES.values():
            arquivo = destino / fonte["arquivo"]
            if (
                not arquivo.is_file()
                or hashlib.sha256(arquivo.read_bytes()).hexdigest() != fonte["sha256"]
            ):
                raise ValueError(f"Fonte existente ausente ou divergente: {arquivo}")
        return destino

    db.PASTA_RAW.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".paradise-", dir=db.PASTA_RAW) as tmp:
        temporario = Path(tmp)
        fontes = temporario / "fontes"
        respostas = temporario / "respostas"
        fontes.mkdir()
        respostas.mkdir()
        manifesto = {"notebook_version": 398, "files": []}
        for nome, fonte in FONTES.items():
            url = BASE_URL + fonte["anexo"]
            with urlopen(url, timeout=60) as resposta:
                original = resposta.read(250_000_001)
            if len(original) > 250_000_000:
                raise ValueError(f"Resposta excede limite de 250 MB: {nome}")
            comprimido = original.startswith(b"\x1f\x8b")
            conteudo = gzip.decompress(original) if comprimido else original
            checksum = hashlib.sha256(conteudo).hexdigest()
            if checksum != fonte["sha256"]:
                raise ValueError(f"SHA-256 divergente: {nome}")
            (fontes / fonte["arquivo"]).write_bytes(conteudo)
            (respostas / (fonte["arquivo"] + ".response")).write_bytes(original)
            manifesto["files"].append(
                {
                    "table": nome,
                    "url": url,
                    "arquivo": fonte["arquivo"],
                    "sha256": checksum,
                    "bytes": len(conteudo),
                    "transport_sha256": hashlib.sha256(original).hexdigest(),
                    "transport_gzip": comprimido,
                }
            )
        (respostas / "manifesto.json").write_text(
            json.dumps(manifesto, indent=2), encoding="utf-8"
        )
        arquivo = raiz / "data" / "pizza_paradise" / f"recepcao-{uuid4().hex}"
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(respostas, arquivo)
        fontes.rename(destino)
    return destino


def main() -> int:
    """CLI de aquisição, sem iniciar carga ou substituir dados existentes."""
    try:
        print(f"Fontes conferidas em {adquirir()}")
        return 0
    except (OSError, ValueError) as erro:
        print(f"Erro na aquisição: {erro}", file=sys.stderr)
        return 1
