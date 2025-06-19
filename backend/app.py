from fastapi import Request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
import os
from backend.services.ib_connection_manager import ib_connection_manager
import asyncio
from fastapi import HTTPException
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Backend starting up...")
    await ib_connection_manager.connect()  # ✅ await required
    asyncio.create_task(ib_connection_manager.start_watchdog())
    yield

    
app = FastAPI(lifespan=lifespan)

# Allow GUI frontend to make requests (on localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TRADES_PATH = Path("backend/config/saved_trades.json")

@app.get("/trades")
def get_trades():
    if not TRADES_PATH.exists():
        return []
    with open(TRADES_PATH, "r") as f:
        return json.load(f)
    
@app.post("/save_trades")
async def save_trades(request: Request):
    data = await request.json()
    with open(TRADES_PATH, "w") as f:
        json.dump(data, f, indent=2)
    return {"message": "Trades saved"}

from backend.services.validation import validate_trade
from backend.services.activation_pipeline import calculate_position_size

@app.post("/activate_trade")
async def activate_trade(request: Request):
    trade = await request.json()

    # ✅ Validate the trade
    errors = validate_trade(trade)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    # ✅ Calculate quantity
    quantity = calculate_position_size(trade)
    if quantity <= 0:
        raise HTTPException(status_code=422, detail={"errors": ["Calculated quantity is zero or negative."]})

    # ✅ Return quantity and mark trade active
    
    return JSONResponse(content={"quantity": quantity})

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
    

@app.get("/status")
async def status():
    try:
        if ib_connection_manager.is_connected():
            return {"status": "connected"}
        else:
            return {"status": "disconnected"}
    except Exception:
        return {"status": "disconnected"}

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

@app.post("/connect_ib")
async def connect_ib():
    async with ib_connection_manager._reconnect_lock:
        await ib_connection_manager.connect()
    await asyncio.sleep(1)
    return {"status": "connected" if ib_connection_manager.is_connected() else "disconnected"}





