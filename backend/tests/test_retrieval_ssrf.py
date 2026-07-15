"""
Frontera anti-SSRF del retrieval (Capa 1A): _host_allowed + fetch_json/text.

Es la superficie de seguridad más sensible del subsistema (ya remediada, pero
sin regresión hasta ahora): que un host FUERA de la whitelist no se pueda pegar.
"""
import pytest
import services.retrieval_service as rs


def test_host_permitido_ok():
    assert rs._host_allowed("https://dolarapi.com/v1/dolares") is True
    assert rs._host_allowed("https://www.bcra.gob.ar/algo") is True


def test_host_no_whitelisteado_rechazado():
    assert rs._host_allowed("https://evil.tld/x") is False
    assert rs._host_allowed("http://169.254.169.254/latest/meta-data/") is False
    assert rs._host_allowed("http://localhost:8000/") is False
    assert rs._host_allowed("http://127.0.0.1/") is False


def test_subdominio_de_atacante_no_pasa():
    # Un host que CONTIENE un dominio permitido pero no ES exacto → rechazado.
    assert rs._host_allowed("https://dolarapi.com.evil.tld/x") is False
    assert rs._host_allowed("https://www.bcra.gob.ar.attacker.com/x") is False
    assert rs._host_allowed("https://notdolarapi.com/x") is False


def test_case_insensitive():
    assert rs._host_allowed("https://DolarAPI.com/x") is True


@pytest.mark.anyio
async def test_fetch_json_rechaza_host_no_permitido():
    with pytest.raises(rs.RetrievalError):
        await rs.fetch_json("https://evil.tld/data")


@pytest.mark.anyio
async def test_fetch_text_rechaza_host_no_permitido():
    with pytest.raises(rs.RetrievalError):
        await rs.fetch_text("http://169.254.169.254/latest/")
