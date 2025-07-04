from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path



from fastapi import Request, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ----------------------- NEW IMPORTS -----------------------
from backend.engine.market_data.factory import get_market_data_client
from backend.engine.tick_handler import TickHandler
from backend.config.settings import get as settings_get

# -----------------------------------------------------------

from backend.services.validation import validate_trade
from backend.routes import ticker_routes
from backend.routes.ticker_routes import build_ticker_payload

from backend.engine.adapters.factory import get_adapter
from backend.engine.trade_manager import TradeManager

exec_adapter = get_adapter(settings_get("execution_adapter", "stub")) 
trade_manager = TradeManager(exec_adapter)
md_client = get_market_data_client(
    settings_get("market_data_provider", "stub")
)
tick_handler: TickHandler | None = None

from backend.engine.order_executor import OrderExecutor

order_executor = OrderExecutor(exec_adapter, trade_manager)


app = FastAPI()

@app.on_event("startup")
async def startup_event() -> None:
    await md_client.connect()              # stub feed starts here
    global tick_handler
    tick_handler = TickHandler(md_client, trade_manager)
    await trade_manager.start()
    # collect every symbol that’s currently in the trade list
    symbols = [t["symbol"] for t in trade_manager.trades]
    await trade_manager.preload_volatility(symbols)
    await exec_adapter.connect()  


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await md_client.disconnect()
    await trade_manager.stop()
    await exec_adapter.disconnect()  

TRADES_PATH = Path("backend/config/saved_trades.json")

def is_valid_trade(trade: dict) -> bool:
    REQUIRED_FIELDS = ["symbol", "name", "last_price"]
    return (
        isinstance(trade, dict) and 
        all(field in trade and trade[field] not in [None, ""] for field in REQUIRED_FIELDS)
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/trades")
def get_trades():
    clean_trades = []
    for trade in trade_manager.trades:
        if isinstance(trade, dict):
            filtered = {}
            for k, v in trade.items():
                if asyncio.iscoroutine(v):
                    continue
                filtered[k] = v
            clean_trades.append(filtered)
    return JSONResponse(content=clean_trades)


@app.post("/save_trades")
async def save_trades(request: Request):
    data = await request.json()
    valid_trades = [t for t in data if is_valid_trade(t)]
    
    # ✅ Save to disk
    with open(TRADES_PATH, "w") as f:
        json.dump(valid_trades, f, indent=2)

    # ✅ Sync backend memory to match GUI save
    trade_manager.trades = valid_trades

    return {
        "message": f"{len(valid_trades)} valid trade(s) saved.",
        "dropped": len(data) - len(valid_trades)
    }


@app.post("/activate_trade")
async def activate_trade(request: Request):
    data = await request.json()
    trade = data.get("trade")
    portfolio = data.get("portfolio")

    errors = validate_trade(trade, portfolio)
    if not errors.get("valid", False):
        raise HTTPException(status_code=422, detail={"errors": errors})

    # ✅ Set trade lifecycle fields
    trade["order_status"] = "Order Active"
    trade["trade_status"] = "Pending"

    # ✅ Load and update saved_trades.json
    if TRADES_PATH.exists():
        with open(TRADES_PATH, "r") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    # ✅ Replace trade if already exists
    existing = [t for t in existing if t.get("symbol") != trade.get("symbol")]
    existing.append(trade)

    with open(TRADES_PATH, "w") as f:
        json.dump(existing, f, indent=2)

    return JSONResponse(content={"message": "Trade validated and activated", "trade": trade})




@app.post("/set_schedule")
async def set_schedule(request: Request):
    data = await request.json()
    reset_time = data.get("reset_time")
    timezone = data.get("timezone")

    if not reset_time or not timezone:
        raise HTTPException(status_code=400, detail="Both reset_time and timezone are required.")

    config_path = os.path.join("backend", "config", "settings.json")

    config = {}
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                pass

    config["reset_time"] = reset_time
    config["timezone"] = timezone

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    return {"message": f"Reset scheduled for {reset_time} ({timezone})"}

@app.get("/get_schedule")
async def get_schedule():
    config_path = os.path.join("backend", "config", "settings.json")

    if not os.path.exists(config_path):
        return {"reset_time": "", "timezone": ""}

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            return {
                "reset_time": config.get("reset_time", ""),
                "timezone": config.get("timezone", "")
            }
    except json.JSONDecodeError:
        return {"reset_time": "", "timezone": ""}


@app.get("/layout_config")
def get_layout_config():
    layout_path = os.path.join("backend", "config", "layout_config.json")
    try:
        with open(layout_path, "r") as f:
            config = json.load(f)
        return JSONResponse(content=config)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/layout_config")
async def update_layout_config(request: Request):
    layout = await request.json()
    layout_path = os.path.join("backend", "config", "layout_config.json")
    with open(layout_path, "w") as f:
        json.dump(layout, f, indent=2)
    return {"status": "success"}

@app.get("/trade_config")
async def get_trade_config():
    path = os.path.join("backend", "config", "trade_config.json")
    with open(path) as f:
        return json.load(f)

@app.post("/trade_config")
async def save_trade_config(request: Request):
    data = await request.json()
    path = os.path.join("backend", "config", "trade_config.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return {"status": "success"}

@app.get("/portfolio_config")
async def get_portfolio_config():
    path = os.path.join("backend", "config", "portfolio_config.json")
    if not os.path.exists(path):
        # Return default structure if file missing
        return {
            "portfolio_value": 0,
            "use_pnl_offset": "No",
            "max_risk": 0
        }

    with open(path) as f:
        return json.load(f)


@app.post("/portfolio_config")
async def save_portfolio_config(request: Request):
    data = await request.json()
    path = os.path.join("backend", "config", "portfolio_config.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return {"status": "success"}


# Mount all API routes from /backend/routes/
app.include_router(ticker_routes.router)


@app.post("/add_trade/{symbol}")
async def add_trade(symbol: str):
    enriched = await build_ticker_payload(symbol)

    if TRADES_PATH.exists():
        with open(TRADES_PATH, "r") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    # Deduplicate and append enriched trade
    existing = [t for t in existing if t.get("symbol") != symbol.upper()]
    existing.append(enriched)

    with open(TRADES_PATH, "w") as f:
        json.dump(existing, f, indent=2)

    return {"message": f"{symbol.upper()} added to saved_trades.json"}

@app.post("/debug/tick")
def debug_tick(symbol: str, price: float):
    trade_manager.evaluate_trade_on_tick(symbol, price)
    return {"message": f"✅ Tick injected for {symbol} at {price}"}


from fastapi import Body

@app.post("/debug/mark_filled")
def debug_mark_filled(data: dict = Body(...)):
    symbol = data["symbol"]
    fill_price = data["fill_price"]
    filled_qty = data["filled_qty"]

    trade_manager.mark_trade_filled(symbol, fill_price, filled_qty)
    return {"message": f"✅ Simulated fill for {symbol} @ ${fill_price} x {filled_qty}"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
