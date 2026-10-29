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

import db

BASE_URL = "https://static.observableusercontent.com/files/"
FONTES = {
    "orders": {
        "arquivo": "orders.parquet",
        "colunas": ["id", "customerId", "storeId", "orderDate", "nItems", "total"],
        "tipos": ["INTEGER", "VARCHAR", "VARCHAR", "VARCHAR", "INTEGER", "DOUBLE"],
        "anexo": (
            "ede989ed5874365bf145962f00a2e8b4024c5d0de663cba68ee28dd66e75d335"
            "3a22a8c00769af5c08c0710c3d0a84834b2006643d65051cb388a20141f56b00"
        ),
        "sha256": "f88d964889bb11dde06b930513ff97bfc407353aedc101f1e4a97bd5acf5947a",
    },
    "order_items": {
        "arquivo": "order_items.parquet",
        "colunas": ["SKU", "orderID"],
        "tipos": ["VARCHAR", "INTEGER"],
        "anexo": (
            "30db2a0090eb4aa564f6d67a152a8a4bedb81bbb42a9c3ab06548b2bc9d5cc73"
            "9472df1b3785570efd376ecc0c8c6629e39a82aeee163d4bc68811360a97d152"
        ),
        "sha256": "cfef82b2403eb04542fa5af10b067dfdb0b45f54bdaa23152c782533fa2b7842",
    },
    "customers": {
        "arquivo": "customers.csv",
        "colunas": ["id", "latitude", "longitude"],
        "anexo": (
            "b6f9dc8144fe510cff0c8368dcf318f169c679581eae2e8ea6d1e5668e1d3343"
            "5d1e46d4e01e867a7438b08f9c57af45e2c3e4ea52d594aec6317c9770c3fb86"
        ),
        "sha256": "a4975208e7d3843fafbd53e5f1ed908530292d7f737ce91453466efa214f0231",
    },
    "stores": {
        "arquivo": "stores.csv",
        "colunas": [
            "id",
            "zipcode",
            "state_abbr",
            "latitude",
            "longitude",
            "city",
            "state",
            "distance",
        ],
        "anexo": (
            "b1837225ab1d3ee4b35b456b576fc971eaa3a0e2ec41da567af29c9cbacbc765"
            "fe7e85db3c0413c1174c1c420ed86d996c4df0c7b49b4bafb899195ba3b5a3b3"
        ),
        "sha256": "48a10f38803de9e904b4cf9a9b9eddc4af29c452e7968f211413bc342655c432",
    },
    "products": {
        "arquivo": "products.csv",
        "colunas": [
            "SKU",
            "Name",
            "Price",
            "Category",
            "Size",
            "Ingredients",
            "Launch",
        ],
        "anexo": (
            "9900712c2f529bb1bab6f2abd1d7b57aa73fdeea1e382628e91bf6a0366532d2"
            "1401aba2b3196a0c611c5a2109b463bf990410000e6aebf51f4fa85f968b10d1"
        ),
        "sha256": "c116092883ee22411c33a9c4a1b0dc68e8df26a26280a50ce10b9097366149e3",
    },
}


def adquirir() -> Path:
    """Obtém as fontes fixadas em specs/ingestao.md, verificando seus hashes.

    Returns:
        Diretório local com as cinco fontes conferidas. Se já existir,
        verifica seu conteúdo sem sobrescrevê-lo ou acessar a rede.

    Raises:
        ValueError: Se um hash divergir, faltar arquivo existente ou uma
            resposta ultrapassar 250 MB.
        OSError: Se houver falha de rede ou de acesso aos arquivos.

    Preserva respostas HTTP e manifesto; publica o diretório de fontes apenas
    depois da validação completa. Não abre nem modifica o banco.
    """
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


if __name__ == "__main__":
    sys.exit(main())
