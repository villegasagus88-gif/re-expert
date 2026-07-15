"""
dolar_service: cotización blue+oficial cacheada, SSRF-safe, best-effort.
"""
import services.dolar_service as ds


class _Resp:
    def __init__(self, status, data):
        self.status_code = status
        self._d = data

    def json(self):
        return self._d


def _reset():
    ds._cache = None
    ds._cache_at = None


async def _fake_ok(url, **kw):
    return _Resp(200, [
        {"casa": "blue", "nombre": "Blue", "compra": 1200, "venta": 1220},
        {"casa": "oficial", "nombre": "Oficial", "compra": 1000, "venta": 1040},
        {"casa": "mep", "nombre": "MEP", "compra": 1150, "venta": 1170},  # se ignora
    ])


async def test_devuelve_blue_y_oficial(monkeypatch):
    _reset()
    monkeypatch.setattr(ds, "safe_get", _fake_ok)
    out = await ds.get_dolar_rates()
    assert out["rates"]["blue"]["venta"] == 1220
    assert out["rates"]["oficial"]["venta"] == 1040
    assert "mep" not in out["rates"]         # solo blue/oficial
    assert out["stale"] is False


async def test_cachea_y_no_repega(monkeypatch):
    _reset()
    calls = {"n": 0}

    async def _counting(url, **kw):
        calls["n"] += 1
        return await _fake_ok(url, **kw)

    monkeypatch.setattr(ds, "safe_get", _counting)
    await ds.get_dolar_rates()
    await ds.get_dolar_rates()
    assert calls["n"] == 1                    # segunda vez desde cache


async def test_fetch_falla_devuelve_stale_o_vacio(monkeypatch):
    _reset()

    async def _boom(url, **kw):
        raise RuntimeError("red caída")

    monkeypatch.setattr(ds, "safe_get", _boom)
    out = await ds.get_dolar_rates()
    assert out["stale"] is True
    assert out["rates"] == {}                 # sin cache previo → vacío, no crash


async def test_stale_usa_ultimo_cache(monkeypatch):
    _reset()
    monkeypatch.setattr(ds, "safe_get", _fake_ok)
    await ds.get_dolar_rates()                # llena cache
    ds._cache_at = None                        # forzar expiración

    async def _boom(url, **kw):
        raise RuntimeError("red caída")

    monkeypatch.setattr(ds, "safe_get", _boom)
    out = await ds.get_dolar_rates()
    assert out["stale"] is True
    assert out["rates"]["blue"]["venta"] == 1220   # devuelve el último conocido
