from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
import os
from backend.engine.ib_client import ib


app = FastAPI()

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
    
from fastapi import Request

@app.post("/save_trades")
async def save_trades(request: Request):
    data = await request.json()
    with open(TRADES_PATH, "w") as f:
        json.dump(data, f, indent=2)
    return {"message": "Trades saved"}

from fastapi import HTTPException
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
    from fastapi.responses import JSONResponse

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
        if ib.isConnected():
            return {"status": "connected"}
        else:
            return {"status": "disconnected"}
    except Exception:
        return {"status": "disconnected"}



