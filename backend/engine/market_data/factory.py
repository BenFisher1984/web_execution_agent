"""
Returns a concrete MarketDataClient based on the nickname in settings.

Usage:
    from backend.engine.market_data.factory import get_market_data_client
    md_client = get_market_data_client("ib")
"""
from __future__ import annotations

from importlib import import_module
from typing import Dict, Type

from backend.engine.market_data.base import MarketDataClient

# Registry.  We'll populate this as we add adapters.
_PROVIDERS: Dict[str, str] = {
    "stub": "backend.engine.market_data.stub_client:StubMarketDataClient",
    # "ib":  "backend.engine.market_data.ib_client:IBMarketDataClient",
    # "polygon": "backend.engine.market_data.polygon_client:PolygonMarketDataClient",
}


def _load(path: str) -> Type[MarketDataClient]:
    module_path, class_name = path.split(":")
    mod = import_module(module_path)
    return getattr(mod, class_name)


def get_market_data_client(name: str) -> MarketDataClient:
    try:
        class_path = _PROVIDERS[name]
    except KeyError:  # pragma: no cover
        raise ValueError(f"Unknown market-data provider '{name}'") from None
    cls = _load(class_path)
    return cls()
