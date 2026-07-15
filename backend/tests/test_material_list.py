"""
Endpoint de la lista de compra de materiales (persistida por usuario).
Se testea el saneo del PUT sin DB real (fake session).
"""
from types import SimpleNamespace
from uuid import uuid4

import pytest
from api.routes.materials import (
    _MATLIST_MAX_QTY,
    MaterialListBody,
    get_material_list,
    put_material_list,
)


class _DB:
    def __init__(self, existing=None):
        self.existing = existing
        self.added = None

    async def get(self, model, pk):
        return self.existing

    def add(self, obj):
        self.added = obj

    async def commit(self):
        pass


@pytest.mark.anyio
async def test_put_sanea_items():
    # Pydantic (dict[str,int]) ya rechaza no-enteros con 422 en el borde; acá
    # se testea el saneo propio del handler: qty<=0 descartado, cap de cantidad.
    db = _DB()
    body = MaterialListBody(items={
        "Cemento": 3,
        "Basura": -5,          # qty<=0 → se descarta
        "Hierro": 999999,      # se capa a _MATLIST_MAX_QTY
    })
    out = await put_material_list(body, user=SimpleNamespace(id=uuid4()), db=db)
    items = db.added.items
    assert items["Cemento"] == 3
    assert "Basura" not in items
    assert items["Hierro"] == _MATLIST_MAX_QTY
    assert out["ok"] is True and out["count"] == 2


@pytest.mark.anyio
async def test_put_actualiza_fila_existente():
    row = SimpleNamespace(items={"viejo": 1})
    db = _DB(existing=row)
    await put_material_list(MaterialListBody(items={"Arena": 2}), user=SimpleNamespace(id=uuid4()), db=db)
    assert row.items == {"Arena": 2}   # pisó la fila existente
    assert db.added is None            # no creó una nueva


@pytest.mark.anyio
async def test_get_sin_fila_devuelve_vacio():
    out = await get_material_list(user=SimpleNamespace(id=uuid4()), db=_DB())
    assert out == {"items": {}}
