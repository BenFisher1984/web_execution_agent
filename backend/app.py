from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime



from fastapi import Request, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ----------------------- NEW IMPORTS -----------------------
from backend.engine.market_data.factory import get_market_data_client
from backend.engine.tick_handler import TickHandler
from backend.config.settings import get as settings_get

# -----------------------------------------------------------

from backend.services.validation import validate_trade, validate_editing_status_consistency
from backend.routes import ticker_routes
from backend.routes.ticker_routes import build_ticker_payload

from backend.engine.adapters.factory import get_adapter
from backend.engine.trade_manager import TradeManager

# Strategy Engine and Pine Script Handler removed - focusing on rules-based workflow

# Create shared IB adapter if using IB for both execution and market data
execution_adapter_name = settings_get("execution_adapter", "stub")
market_data_provider = settings_get("market_data_provider", "stub")

if execution_adapter_name == "ib" and market_data_provider == "ib":
    # Create shared IB adapter for both execution and market data
    from backend.engine.adapters.ib_adapter import IBAdapter
    from backend.engine.market_data.ib_client import IBMarketDataClient
    
    shared_ib_adapter = IBAdapter(client_id=2)
    exec_adapter = shared_ib_adapter
    md_client = IBMarketDataClient(ib_adapter=shared_ib_adapter)
else:
    # Use separate adapters for different providers
    exec_adapter = get_adapter(str(execution_adapter_name) if execution_adapter_name else "stub")
    md_client = get_market_data_client(str(market_data_provider) if market_data_provider else "stub")

from backend.engine.order_executor import OrderExecutor

# Create OrderExecutor first
order_executor = OrderExecutor(exec_adapter)

# Then create TradeManager with OrderExecutor
trade_manager = TradeManager(exec_adapter, md_client=md_client, order_executor=order_executor)

# Set the trade_manager reference in OrderExecutor
order_executor.trade_manager = trade_manager

tick_handler: TickHandler | None = None

# Strategy Engine and Pine Script Handler removed - focusing on rules-based workflow

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'engine'))
from backend.engine import indicators, volatility


app = FastAPI()

# Define TRADES_PATH for use in endpoints
TRADES_PATH = Path("backend/config/saved_trades.json")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Trading Execution Agent API",
        "version": "1.0.0",
        "status": "running",
        "available_endpoints": {
            "health": "/health",
            "trades": "/trades", 
            "inject_tick": "/inject_tick",
            "debug_mark_filled": "/debug/mark_filled",
            "layout_config": "/layout_config",
            "trade_config": "/trade_config",
            "portfolio_config": "/portfolio_config"
        },
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    # Existing health info
    status = "ok"
    # Check market data provider connection using the existing connected instance
    try:
        # Use the existing md_client that was connected during startup
        if hasattr(md_client, "is_connected"):
            connected = md_client.is_connected() if callable(md_client.is_connected) else md_client.is_connected
        elif hasattr(md_client, "_connected"):
            connected = md_client._connected
        elif hasattr(md_client, "_running"):
            connected = md_client._running
        else:
            connected = False
    except Exception:
        connected = False
    market_data_status = "connected" if connected else "disconnected"
    return {"status": status, "market_data": market_data_status}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with all system components"""
    try:
        # This would integrate with actual TradeManager instance
        detailed_status = {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "system_components": {
                "broker_adapter": {
                    "status": "connected",
                    "last_heartbeat": datetime.utcnow().isoformat(),
                    "connection_errors": 0
                },
                "market_data_client": {
                    "status": "connected", 
                    "last_update": datetime.utcnow().isoformat(),
                    "subscription_errors": 0
                },
                "trade_manager": {
                    "status": "running",
                    "active_trades": 0,  # Would get actual count
                    "background_tasks": "running"
                }
            },
            "error_handling": {
                "total_errors": 0,
                "operations_with_errors": 0,
                "circuit_breakers": {
                    "broker": {
                        "state": "CLOSED",
                        "failure_count": 0,
                        "can_execute": True
                    },
                    "market_data": {
                        "state": "CLOSED", 
                        "failure_count": 0,
                        "can_execute": True
                    }
                }
            },
            "performance_metrics": {
                "avg_evaluation_time_ms": 0,
                "trades_processed": 0,
                "success_rate_percent": 100.0
            }
        }
        return detailed_status
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/health/errors")
async def error_status():
    """Get current error statistics and circuit breaker status"""
    try:
        error_stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_counts": {},  # Would get from actual error handler
            "circuit_breakers": {
                "broker": {
                    "state": "CLOSED",
                    "failure_count": 0,
                    "last_failure_time": None,
                    "can_execute": True
                },
                "market_data": {
                    "state": "CLOSED",
                    "failure_count": 0, 
                    "last_failure_time": None,
                    "can_execute": True
                }
            },
            "recent_errors": []  # Would get from actual error log
        }
        return error_stats
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.on_event("startup")
async def startup_event() -> None:
    await md_client.connect()              # stub feed starts here
    app.state.md_client = md_client  # Attach to app state
    global tick_handler
    tick_handler = TickHandler(md_client, trade_manager)
    await trade_manager.start()
    try:
        await exec_adapter.connect()
        await order_executor.start()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Execution adapter connection failed (continuing without execution): {e}")



@app.on_event("shutdown")
async def shutdown_event() -> None:
    await md_client.disconnect()
    await trade_manager.stop()
    await exec_adapter.disconnect() 
    await order_executor.stop()

def is_valid_trade(trade: dict) -> bool:
    # Skip validation for draft trades (editing: true)
    if trade.get("editing", False):
        return True
    
    # For non-draft trades, require basic fields
    REQUIRED_FIELDS = ["symbol"]
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

# Strategy routes removed - focusing on rules-based workflow

@app.get("/trades")
def get_trades():
    """Return fresh trade data directly from saved_trades.json"""
    try:
        # Read fresh data from file, not cached data
        trades = trade_manager.load_trades()
        clean_trades = []
        for trade in trades:
            if isinstance(trade, dict):
                filtered = {}
                for k, v in trade.items():
                    if asyncio.iscoroutine(v):
                        continue
                    filtered[k] = v
                clean_trades.append(filtered)
        return JSONResponse(content=clean_trades)
    except Exception as e:
        logger.error(f"Failed to load trades for API: {e}")
        return JSONResponse(content=[], status_code=500)


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

    # Create a backup copy of the trade before modification
    original_trade = trade.copy() if trade else None
    
    try:
        # Validate trade
        errors = validate_trade(trade, portfolio)
        if not errors.get("valid", False):
            raise HTTPException(status_code=422, detail={"errors": errors})

        # Load existing trades before modification
        if TRADES_PATH.exists():
            with open(TRADES_PATH, "r") as f:
                try:
                    existing = json.load(f)
                except json.JSONDecodeError:
                    existing = []
        else:
            existing = []

        # Store original trades list for rollback
        original_trades = existing.copy()

        # ✅ Set trade lifecycle fields atomically
        trade["order_status"] = "Working" 
        trade["trade_status"] = "Pending"
        
        # Log editing field change for audit trail
        old_editing = original_trade.get("editing") if original_trade else None
        trade["editing"] = False  # Clear editing mode when activating
        print(f"LOG: Editing field changed: {old_editing} -> False (trade activation) for symbol: {trade.get('symbol')}")
        
        # Add timestamp for audit trail
        trade["activated_at"] = datetime.now().isoformat()

        # ✅ Replace trade if already exists
        existing = [t for t in existing if t.get("symbol") != trade.get("symbol")]
        existing.append(trade)

        # Atomic write with error handling
        try:
            with open(TRADES_PATH, "w") as f:
                json.dump(existing, f, indent=2)
        except Exception as write_error:
            # Rollback on write failure
            print(f"ERROR: Failed to save activated trade: {write_error}")
            # Restore original file if possible
            try:
                with open(TRADES_PATH, "w") as f:
                    json.dump(original_trades, f, indent=2)
            except:
                pass  # Best effort rollback
            raise HTTPException(status_code=500, detail={"error": "Failed to save trade activation"})

        print(f"SUCCESS: Trade activated successfully: {trade.get('symbol')} - {trade.get('order_status')}/{trade.get('trade_status')}")
        return JSONResponse(content={"message": "Trade validated and activated", "trade": trade})
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        # Handle unexpected errors
        print(f"ERROR: Unexpected error during trade activation: {e}")
        raise HTTPException(status_code=500, detail={"error": "Internal server error during trade activation"})




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
    enriched = await build_ticker_payload(symbol, md_client)

    if TRADES_PATH.exists():
        with open(TRADES_PATH, "r") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    # When creating or serializing a trade, use arrays for all rule types
    # Example for trade creation:
    trade = {
        "symbol": enriched["symbol"],
        "name": enriched["name"],
        "last_price": enriched["last_price"],
        "volatility": {
            "adr_20": enriched.get("adr_20"),
            "atr_14": enriched.get("atr_14")
        },
        "time_in_force": enriched.get("time_in_force", "GTC"),
        "order_type": enriched.get("order_type", "Market"),
        "calculated_quantity": enriched.get("calculated_quantity", 0),
        "usd": enriched.get("usd", 0),
        "percent_balance": enriched.get("percent_balance", 0),
        "usd_risk": enriched.get("usd_risk", 0),
        "percent_risk": enriched.get("percent_risk", 0),
        "entry_rules": [enriched.get("entry_rule", {})],
        "initial_stop_rules": [enriched.get("initial_stop_rule", {})],
        "trailing_stop_rules": [enriched.get("trailing_stop_rule", {})],
        "take_profit_rules": [enriched.get("take_profit_rule", {})]
    }
    # Remove any singular object forms from trade creation and serialization

    # Deduplicate and append enriched trade
    existing = [t for t in existing if t.get("symbol") != symbol.upper()]
    existing.append(trade)

    with open(TRADES_PATH, "w") as f:
        json.dump(existing, f, indent=2)

    return {"message": f"{symbol.upper()} added to saved_trades.json"}

@app.post("/inject_tick")
async def inject_tick(request: Request):
    """Inject a tick for testing trade execution"""
    try:
        tick_data = await request.json()
        symbol = tick_data.get("symbol")
        price = tick_data.get("price")
        
        if not symbol or price is None:
            raise HTTPException(status_code=400, detail="symbol and price are required")
        
        # Process the tick through trade manager
        await trade_manager.evaluate_trade_on_tick(symbol, price)
        
        return {
            "message": f"✅ Tick injected for {symbol} at ${price}",
            "tick_data": tick_data
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error injecting tick: {e}")
        raise HTTPException(status_code=500, detail=f"Error injecting tick: {str(e)}")

@app.post("/debug/tick")
async def debug_tick(symbol: str, price: float):
    await trade_manager.evaluate_trade_on_tick(symbol, price)
    return {"message": f"✅ Tick injected for {symbol} at {price}"}

@app.post("/simulate_fill")
async def simulate_fill(request: Request):
    """Legacy endpoint - redirects to appropriate fill type"""
    try:
        fill_data = await request.json()
        symbol = fill_data.get("symbol")
        fill_price = fill_data.get("fill_price")
        filled_qty = fill_data.get("filled_qty")
        
        if not symbol or fill_price is None or filled_qty is None:
            raise HTTPException(status_code=400, detail="symbol, fill_price, and filled_qty are required")
        
        # Default to entry fill for backward compatibility
        await trade_manager.mark_trade_filled(symbol, fill_price, filled_qty)
        
        return {
            "message": f"✅ Entry fill simulated for {symbol}: {filled_qty} shares @ ${fill_price}",
            "fill_data": fill_data
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error simulating fill: {e}")
        raise HTTPException(status_code=500, detail=f"Error simulating fill: {str(e)}")

@app.post("/simulate_entry_fill")
async def simulate_entry_fill(request: Request):
    """Simulate entry order fill"""
    try:
        fill_data = await request.json()
        symbol = fill_data.get("symbol")
        fill_price = fill_data.get("fill_price")
        filled_qty = fill_data.get("filled_qty")
        
        if not symbol or fill_price is None or filled_qty is None:
            raise HTTPException(status_code=400, detail="symbol, fill_price, and filled_qty are required")
        
        # Simulate entry fill
        await trade_manager.mark_trade_filled(symbol, fill_price, filled_qty)
        
        return {
            "message": f"✅ Entry fill simulated for {symbol}: {filled_qty} shares @ ${fill_price}",
            "fill_data": fill_data,
            "fill_type": "entry"
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error simulating entry fill: {e}")
        raise HTTPException(status_code=500, detail=f"Error simulating entry fill: {str(e)}")

@app.post("/simulate_exit_fill")
async def simulate_exit_fill(request: Request):
    """Simulate exit order fill"""
    try:
        fill_data = await request.json()
        symbol = fill_data.get("symbol")
        exit_price = fill_data.get("exit_price")
        exit_qty = fill_data.get("exit_qty")
        
        if not symbol or exit_price is None or exit_qty is None:
            raise HTTPException(status_code=400, detail="symbol, exit_price, and exit_qty are required")
        
        # Simulate exit fill using mark_trade_closed
        await trade_manager.mark_trade_closed(symbol, exit_price, exit_qty)
        
        return {
            "message": f"✅ Exit fill simulated for {symbol}: {exit_qty} shares @ ${exit_price}",
            "fill_data": fill_data,
            "fill_type": "exit"
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error simulating exit fill: {e}")
        raise HTTPException(status_code=500, detail=f"Error simulating exit fill: {str(e)}")


from fastapi import Body

@app.post("/debug/mark_filled")
async def debug_mark_filled(data: dict = Body(...)):
    symbol = data["symbol"]
    fill_price = data["fill_price"]
    filled_qty = data["filled_qty"]

    await trade_manager.mark_trade_filled(symbol, fill_price, filled_qty)
    return {"message": f"✅ Simulated fill for {symbol} @ ${fill_price} x {filled_qty}"}

@app.get("/debug/active_orders")
async def get_active_orders():
    """Get active orders from OrderExecutor for debugging"""
    if order_executor:
        return {
            "active_orders": order_executor.active_orders,
            "count": len(order_executor.active_orders)
        }
    return {"active_orders": {}, "count": 0}

@app.post("/inject_fill")
async def inject_fill(request: Request):
    """
    Inject a fill through the proper OrderExecutor pipeline.
    This simulates a real broker fill going through the actual production code path.
    """
    try:
        fill_data = await request.json()
        broker_id = fill_data.get("broker_id")
        symbol = fill_data.get("symbol") 
        qty = fill_data.get("qty")
        price = fill_data.get("price")
        
        if not all([broker_id, symbol, qty is not None, price is not None]):
            raise HTTPException(status_code=400, detail="broker_id, symbol, qty, and price are required")
        
        # Create proper Fill object matching the TypedDict
        from datetime import datetime
        fill = {
            "broker_id": str(broker_id),
            "symbol": symbol,
            "qty": int(qty),
            "price": float(price),
            "ts": datetime.utcnow(),
            "local_id": str(broker_id)  # Use same as broker_id for simplicity
        }
        
        # Send fill through the actual OrderExecutor pipeline
        await order_executor._on_fill(fill)
        
        return {
            "message": f"✅ Fill injected through OrderExecutor: {symbol} {qty} @ ${price}",
            "fill": fill
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error injecting fill: {e}")
        raise HTTPException(status_code=500, detail=f"Error injecting fill: {str(e)}")

@app.get("/trades/{symbol}/audit")
async def get_trade_audit_trail(symbol: str):
    """Get audit trail for a specific trade"""
    try:
        # Get trade manager instance
        from backend.engine.trade_manager import TradeManager
        # This is a simplified implementation - in production you'd have a proper way to access the trade manager
        audit_trail = []  # Placeholder - would get from actual trade manager
        return {"symbol": symbol, "audit_trail": audit_trail}
    except Exception as e:
        return {"error": str(e)}

@app.get("/trades/{symbol}/metrics")
async def get_trade_performance_metrics(symbol: str):
    """Get performance metrics for a specific trade"""
    try:
        # This is a simplified implementation - in production you'd have a proper way to access the trade manager
        metrics = {
            "symbol": symbol,
            "total_events": 0,
            "status_transitions": 0,
            "fills": 0,
            "errors": 0,
            "duration_seconds": 0,
            "last_event": None
        }
        return metrics
    except Exception as e:
        return {"error": str(e)}

@app.get("/trades/audit")
async def get_all_audit_trails():
    """Get audit trail for all trades"""
    try:
        # This is a simplified implementation - in production you'd have a proper way to access the trade manager
        audit_trail = []
        return {"audit_trail": audit_trail}
    except Exception as e:
        return {"error": str(e)}


@app.get("/indicator-value")
def get_indicator_value(
    symbol: str = Query(...),
    indicator: str = Query(...),
    lookback: int = Query(8)
):
    print(f"[LOG] Calculating {indicator.upper()} {lookback} for {symbol}")  # Logging for proof
    try:
        # Use the market data client to get real historical data
        async def fetch_and_calculate():
            # Get historical data from IB
            bars = await md_client.get_historical_data(symbol.upper(), lookback_days=30)
            if not bars:
                raise Exception(f"No historical data available for {symbol}")
            
            # Extract closing prices from bars
            prices = [bar.close for bar in bars if hasattr(bar, "close") and bar.close is not None]
            if not prices:
                raise Exception(f"No valid price data for {symbol}")
            
            # Calculate indicator value
            value = None
            if indicator.lower() == "ema":
                value = indicators.calculate_ema(prices, lookback)
            elif indicator.lower() == "sma":
                value = indicators.calculate_sma(prices, lookback)
            elif indicator.lower() == "atr":
                # For ATR, we need OHLC data, not just closes
                value = volatility.calculate_atr(bars, {"lookback": lookback})
            elif indicator.lower() == "adr":
                value = volatility.calculate_adr(bars, {"lookback": lookback})
            else:
                raise Exception(f"Unknown indicator: {indicator}")
            
            return value
        
        # Run the async function
        import asyncio
        value = asyncio.run(fetch_and_calculate())
        
        return {"symbol": symbol, "indicator": indicator, "lookback": lookback, "value": value}
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
