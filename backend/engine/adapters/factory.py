"""
backend/engine/adapters/factory.py

Returns a live AdapterBase instance based on the short broker name.
"""
from __future__ import annotations

from importlib import import_module
from typing import Dict, Type

from backend.engine.adapters.base import BrokerAdapter

_PROVIDERS = {
    "stub": "backend.engine.adapters.stub_adapter:StubExecutionAdapter",
    "ib":   "backend.engine.adapters.ib_adapter:IbExecutionAdapter",
}


def _load(path: str) -> Type[BrokerAdapter]:
    module_path, class_name = path.split(":")
    mod = import_module(module_path)
    return getattr(mod, class_name)

def get_adapter(name: str) -> BrokerAdapter:
    try:
        class_path = _PROVIDERS[name]
    except KeyError:  # pragma: no cover
        raise ValueError(f"Unknown execution adapter '{name}'") from None
    cls = _load(class_path)
    return cls()
