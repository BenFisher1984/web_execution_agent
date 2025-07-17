from fastapi import APIRouter, HTTPException, Request
from backend.engine.volatility import calculate_adr, calculate_atr
from backend.engine.market_data.factory import get_market_data_client
from backend.config.settings import get as settings_get
from backend.services.validation import validate_trade
import os
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

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
                        key = field["key"]
                        vol_type = field["volatility_type"]
                        lookback = field["lookback"]
                        lookbacks[key] = (vol_type, lookback)
    except Exception as e:
        logger.warning(f"⚠️ Failed to parse layout_config.json: {e}")
    return lookbacks

async def build_ticker_payload(symbol: str, md_client) -> dict:
    # md_client is now passed in from the route
    try:
        contract = await md_client.get_contract_details(symbol)
        if not contract:
            raise HTTPException(status_code=404, detail="Symbol not found")

        # using the contract, get extra details if needed
        long_name = getattr(contract, "symbol", symbol.upper())

        last = await md_client.get_last_price(symbol)
        if last is None or last == 0:
            raise HTTPException(status_code=400, detail="No market data available")

        # Get historical data for volatility calculations only (not for storage)
        bars = await md_client.get_historical_data(symbol, lookback_days=30)
        if not bars:
            raise HTTPException(status_code=400, detail="No historical data available")

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
            **flat_volatility
            # Removed historical_closes - no longer storing historical data in JSON
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building ticker payload for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/ticker/{symbol}")
async def get_ticker_info(symbol: str, request: Request):
    try:
        md_client = request.app.state.md_client
        payload = await build_ticker_payload(symbol, md_client)
        logger.info(f"✅ /ticker response: {payload}")
        return payload
    except Exception as e:
        logger.error(f"❌ Exception in /ticker: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate_trade")
async def validate_trade_route(request: Request):
    payload = await request.json()
    trade = payload.get("trade", {})
    portfolio = payload.get("portfolio", {})
    logger.debug(f"🔍 Received portfolio: {portfolio}")
    result = validate_trade(trade, portfolio)
    return result

# rules routes kept identical
rules_router = APIRouter()
INDICATOR_CONFIG_PATH = os.path.join("backend", "config", "indicators_config.json")

@rules_router.get("/indicators_config")
async def get_indicators_config():
    with open(INDICATOR_CONFIG_PATH) as f:
        return json.load(f)
