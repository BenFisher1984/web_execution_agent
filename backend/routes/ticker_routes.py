from fastapi import APIRouter, HTTPException
from backend.engine.volatility import calculate_adr, calculate_atr
from backend.engine.ib_client import ib_client
import os, json

router = APIRouter()
LAYOUT_CONFIG_PATH = os.path.join("backend", "config", "layout_config.json")


def get_enabled_volatility_lookbacks():
    lookbacks = {}
    try:
        with open(LAYOUT_CONFIG_PATH) as f:
            layout = json.load(f)
            for section in layout:
                for field in section.get("fields", []):
                    if (
                        field.get("key", "").startswith("volatility.") and
                        field.get("type") == "readonly" and
                        field.get("enabled", True) and
                        "lookback" in field and
                        "volatility_type" in field
                    ):
                        key = field["key"]  # e.g. "volatility.adr_20"
                        vol_type = field["volatility_type"]
                        lookback = field["lookback"]
                        lookbacks[key] = (vol_type, lookback)
    except Exception as e:
        print(f"⚠️ Failed to parse layout_config.json: {e}")
    return lookbacks


async def build_ticker_payload(symbol: str) -> dict:
    contract = await ib_client.get_contract_details(symbol)
    if not contract:
        raise HTTPException(status_code=404, detail="Symbol not found")

    details = await ib_client.ib.reqContractDetailsAsync(contract)
    long_name = (
        details[0].longName if details and getattr(details[0], "longName", None)
        else contract.symbol
    )

    last = await ib_client.get_last_price(symbol)
    if last is None:
        raise HTTPException(status_code=400, detail="No market data available")

    bars = await ib_client.get_historical_data(symbol, lookback_days=30)
    if not bars:
        raise HTTPException(status_code=400, detail="No historical data available")
    
    # extract closing prices from bars
    historical_closes = [bar.close for bar in bars if bar.close is not None]


    volatility_fields = get_enabled_volatility_lookbacks()
    flat_volatility = {}

    for flat_key, (vol_type, lookback) in volatility_fields.items():
        if vol_type == "adr":
            val = calculate_adr(bars, options={"lookback": lookback})
        elif vol_type == "atr":
            val = calculate_atr(bars, options={"lookback": lookback})
        else:
            val = None
        flat_volatility[flat_key] = float(val) if val is not None else None

    return {
        "symbol": symbol.upper(),
        "name": long_name,
        "last_price": last,
        **flat_volatility,
        "historical_closes": historical_closes
    }


@router.get("/ticker/{symbol}")
async def get_ticker_info(symbol: str):
    try:
        payload = await build_ticker_payload(symbol)
        print("✅ /ticker response:", payload)
        return payload
    except Exception as e:
        print(f"❌ Exception in /ticker: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
from fastapi import Request
from backend.services.validation import validate_trade

@router.post("/validate_trade")
async def validate_trade_route(request: Request):
    payload = await request.json()
    trade = payload.get("trade", {})
    portfolio = payload.get("portfolio", {})
    # 🧪 Add this
    print("🔍 Received portfolio:", portfolio)
    result = validate_trade(trade, portfolio)
    return result

from fastapi import APIRouter
import json
import os

rules_router = APIRouter()
INDICATOR_CONFIG_PATH = os.path.join("backend", "config", "indicators_config.json")

@rules_router.get("/indicators_config")
async def get_indicators_config():
    with open(INDICATOR_CONFIG_PATH) as f:
        return json.load(f)
