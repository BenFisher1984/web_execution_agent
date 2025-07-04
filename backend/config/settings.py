"""
backend/config/settings.py

Loads settings.json once at import-time and exposes:

    get(key, default=None)   -- convenience accessor
    data                     -- raw dict if you need everything
"""
from __future__ import annotations

import json
from pathlib import Path

_cfg_path = Path(__file__).with_suffix(".json")   # same folder → settings.json
with _cfg_path.open(encoding="utf-8") as f:
    _data: dict = json.load(f)

def get(key: str, default=None):
    return _data.get(key, default)

data = _data          # optional: import settings.data for the whole dict
settings = _data

