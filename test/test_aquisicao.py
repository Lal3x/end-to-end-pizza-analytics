"""Aquisição com respostas sintéticas; nenhuma rede obrigatória."""

import gzip
import hashlib
import io
import json

import pytest

import baixar_dados as aquisicao
import db


def configurar(tmp_path, monkeypatch, corromper=False):
    fontes = {
        "a": {
            "arquivo": "a.csv",
            "anexo": "a",
            "sha256": hashlib.sha256(b"id\n001\n").hexdigest(),
        },
        "b": {
            "arquivo": "b.parquet",
            "anexo": "b",
            "sha256": hashlib.sha256(b"conteudo binario").hexdigest(),
        },
    }
    respostas = {
        aquisicao.BASE_URL + "a": gzip.compress(b"id\n001\n"),
        aquisicao.BASE_URL + "b": b"incorreto" if corromper else b"conteudo binario",
    }
    monkeypatch.setattr(db, "PASTA_RAW", tmp_path / "raw")
    monkeypatch.setattr(aquisicao, "FONTES", fontes)
    monkeypatch.setattr(
        aquisicao, "urlopen", lambda url, timeout: io.BytesIO(respostas[url])
    )


def test_aquisicao_preserva_transporte_valida_hash_e_reexecucao(tmp_path, monkeypatch):
    configurar(tmp_path, monkeypatch)
    destino = aquisicao.adquirir()
    assert (destino / "a.csv").read_bytes() == b"id\n001\n"
    assert (destino / "b.parquet").read_bytes() == b"conteudo binario"
    arquivos = list((tmp_path / "data" / "pizza_paradise").glob("recepcao-*"))
    assert len(arquivos) == 1
    manifesto = json.loads((arquivos[0] / "manifesto.json").read_text())
    assert manifesto["files"][0]["transport_gzip"] is True
    assert (
        gzip.decompress((arquivos[0] / "a.csv.response").read_bytes()) == b"id\n001\n"
    )
    assert aquisicao.adquirir() == destino
    assert aquisicao.main() == 0


def test_hash_divergente_nao_publica_fontes_parciais(tmp_path, monkeypatch):
    configurar(tmp_path, monkeypatch, corromper=True)
    with pytest.raises(ValueError, match="SHA-256 divergente: b"):
        aquisicao.adquirir()
    assert not (tmp_path / "raw" / "pizza_paradise").exists()
    assert aquisicao.main() == 1


def test_fonte_existente_divergente_nao_e_sobrescrita(tmp_path, monkeypatch):
    configurar(tmp_path, monkeypatch)
    destino = aquisicao.adquirir()
    (destino / "a.csv").write_bytes(b"alterado")
    with pytest.raises(ValueError, match="divergente"):
        aquisicao.adquirir()
    assert (destino / "a.csv").read_bytes() == b"alterado"
