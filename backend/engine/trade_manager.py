from backend.engine.adapters.base import BrokerAdapter
from backend.engine.volatility import calculate_adr, calculate_atr
import json
import os
import math
import time
from datetime import datetime
import asyncio
import statistics
import logging
from typing import Optional, Dict, Any, Tuple, List
from backend.config.status_enums import OrderStatus, TradeStatus
from .entry_evaluator import EntryEvaluator
from .stop_loss_evaluator import StopLossEvaluator
from .take_profit_evaluator import TakeProfitEvaluator
from .trailing_stop_evaluator import TrailingStopEvaluator
from .portfolio_evaluator import PortfolioEvaluator
from .indicators import build_preloaded_rolling_window

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Centralized error handling with retry logic and graceful degradation.
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.error_counts: Dict[str, int] = {}
        
    async def execute_with_retry(self, operation_name: str, operation, *args, **kwargs):
        """
        Execute operation with retry logic and error tracking.
        
        Args:
            operation_name: Name of the operation for logging
            operation: Async function to execute
            *args, **kwargs: Arguments for the operation
            
        Returns:
            Result of the operation or None if all retries failed
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                
                # Reset error count on success
                self.error_counts[operation_name] = 0
                logger.info(f"✅ {operation_name} completed successfully")
                return result
                
            except Exception as e:
                last_error = e
                self.error_counts[operation_name] = self.error_counts.get(operation_name, 0) + 1
                
                error_msg = f"❌ {operation_name} failed (attempt {attempt + 1}/{self.max_retries + 1}): {str(e)}"
                
                if attempt < self.max_retries:
                    logger.warning(f"{error_msg} - Retrying in {self.retry_delay}s...")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"{error_msg} - All retries exhausted")
                    
        # Log final failure
        logger.error(f"🚨 {operation_name} failed permanently after {self.max_retries + 1} attempts: {last_error}")
        return None
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        return {
            "error_counts": self.error_counts.copy(),
            "total_errors": sum(self.error_counts.values()),
            "operations_with_errors": len([k for k, v in self.error_counts.items() if v > 0])
        }


class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls.
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def record_failure(self):
        """Record a failure and potentially open the circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"🚨 Circuit breaker OPENED after {self.failure_count} failures")
    
    def record_success(self):
        """Record a success and potentially close the circuit"""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("✅ Circuit breaker CLOSED after successful recovery")
    
    def can_execute(self) -> bool:
        """Check if operation can be executed based on circuit breaker state"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            # Check if recovery timeout has passed
            if self.last_failure_time and time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("🔄 Circuit breaker moved to HALF_OPEN state")
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "can_execute": self.can_execute()
        }


class TradeLifecycleLogger:
    """
    Professional trade lifecycle monitoring and audit trail.
    Tracks all status transitions with structured logging.
    """
    
    def __init__(self, log_file: str = "trade_lifecycle.log"):
        self.log_file = log_file
        self.audit_trail: List[Dict[str, Any]] = []
        
    def log_status_transition(self, 
                            trade_id: str, 
                            symbol: str, 
                            from_status: str, 
                            to_status: str, 
                            trigger: str, 
                            context: Optional[Dict[str, Any]] = None):
        """
        Log a status transition with structured data.
        
        Args:
            trade_id: Unique trade identifier
            symbol: Trading symbol
            from_status: Previous status
            to_status: New status
            trigger: What caused the transition
            context: Additional context (price, quantity, etc.)
        """
        timestamp = datetime.utcnow().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "trade_id": trade_id,
            "symbol": symbol,
            "from_status": from_status,
            "to_status": to_status,
            "trigger": trigger,
            "context": context or {},
            "event_type": "status_transition"
        }
        
        # Add to audit trail
        self.audit_trail.append(log_entry)
        
        # Structured logging
        logger.info(
            f"TRADE_LIFECYCLE: {symbol} | {from_status} → {to_status} | Trigger: {trigger}",
            extra={
                "trade_id": trade_id,
                "symbol": symbol,
                "from_status": from_status,
                "to_status": to_status,
                "trigger": trigger,
                "context": context or {},
                "event_type": "status_transition"
            }
        )
        
        # Save to file for persistence
        self._save_audit_entry(log_entry)
    
    def log_trade_event(self, 
                       trade_id: str, 
                       symbol: str, 
                       event_type: str, 
                       event_data: Dict[str, Any]):
        """
        Log a trade-related event (fills, errors, etc.).
        
        Args:
            trade_id: Unique trade identifier
            symbol: Trading symbol
            event_type: Type of event (fill, error, etc.)
            event_data: Event-specific data
        """
        timestamp = datetime.utcnow().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "trade_id": trade_id,
            "symbol": symbol,
            "event_type": event_type,
            "event_data": event_data
        }
        
        # Add to audit trail
        self.audit_trail.append(log_entry)
        
        # Structured logging
        logger.info(
            f"TRADE_EVENT: {symbol} | {event_type}",
            extra={
                "trade_id": trade_id,
                "symbol": symbol,
                "event_type": event_type,
                "event_data": event_data
            }
        )
        
        # Save to file for persistence
        self._save_audit_entry(log_entry)
    
    def _save_audit_entry(self, entry: Dict[str, Any]):
        """Save audit entry to file"""
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to save audit entry: {e}")
    
    def get_audit_trail(self, symbol: Optional[str] = None, trade_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get audit trail filtered by symbol or trade_id"""
        if symbol:
            return [entry for entry in self.audit_trail if entry.get("symbol") == symbol]
        elif trade_id:
            return [entry for entry in self.audit_trail if entry.get("trade_id") == trade_id]
        return self.audit_trail
    
    def get_trade_performance_metrics(self, symbol: str) -> Dict[str, Any]:
        """Calculate performance metrics for a trade"""
        trade_events = self.get_audit_trail(symbol=symbol)
        
        if not trade_events:
            return {}
        
        # Calculate metrics
        status_transitions = [e for e in trade_events if e.get("event_type") == "status_transition"]
        fills = [e for e in trade_events if e.get("event_type") == "fill"]
        errors = [e for e in trade_events if e.get("event_type") == "error"]
        
        # Time-based metrics
        if status_transitions:
            first_event = min(status_transitions, key=lambda x: x["timestamp"])
            last_event = max(status_transitions, key=lambda x: x["timestamp"])
            
            start_time = datetime.fromisoformat(first_event["timestamp"])
            end_time = datetime.fromisoformat(last_event["timestamp"])
            duration = (end_time - start_time).total_seconds()
        else:
            duration = 0
        
        return {
            "symbol": symbol,
            "total_events": len(trade_events),
            "status_transitions": len(status_transitions),
            "fills": len(fills),
            "errors": len(errors),
            "duration_seconds": duration,
            "last_event": trade_events[-1]["timestamp"] if trade_events else None
        }


class TradeManager:
    """
    Central orchestrator for trade lifecycle management.
    Coordinates all evaluators and manages parent/child order framework.
    """
    
    def __init__(self, exec_adapter: BrokerAdapter, md_client=None, order_executor=None, 
                 config_path="backend/config/saved_trades.json", enable_tasks=True):
        self.adapter = exec_adapter
        self.md_client = md_client  # Market data client for historical data
        self.order_executor = order_executor
        self.config_path = config_path
        self.trades = self.load_trades()
        self.save_pending = False
        self.save_delay = 1.0
        self.volatility_cache: dict[str, dict] = {}
        self.contract_details: dict[str, dict] = {}
        self._debounce_task = None
        self._sync_task = None

        # Initialize error handling components
        self.error_handler = ErrorHandler(max_retries=3, retry_delay=1.0)
        self.broker_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
        self.market_data_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        
        # Initialize lifecycle logger
        self.lifecycle_logger = TradeLifecycleLogger()

        # Initialize evaluators
        self.entry_evaluator = EntryEvaluator()
        self.stop_loss_evaluator = StopLossEvaluator()
        self.take_profit_evaluator = TakeProfitEvaluator()
        self.trailing_stop_evaluator = TrailingStopEvaluator()
        self.portfolio_evaluator = PortfolioEvaluator()
        
        # Background tasks
        if enable_tasks:
            self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background tasks for trade management"""
        logger.info("🔄 Starting TradeManager background tasks")
        # Background tasks will be started in the start() method

    def _generate_trade_id(self, symbol: str) -> str:
        """Generate unique trade ID"""
        timestamp = int(time.time())
        return f"{symbol}_{timestamp}"

    def _log_status_transition(self, trade: dict, from_status: str, to_status: str, trigger: str, context: Optional[Dict[str, Any]] = None):
        """Log a status transition with proper trade ID"""
        symbol = trade.get("symbol", "unknown")
        trade_id = trade.get("trade_id") or self._generate_trade_id(symbol)
        
        # Ensure trade has a trade_id
        if not trade.get("trade_id"):
            trade["trade_id"] = trade_id
        
        self.lifecycle_logger.log_status_transition(
            trade_id=trade_id,
            symbol=symbol,
            from_status=from_status,
            to_status=to_status,
            trigger=trigger,
            context=context
        )

    def _log_trade_event(self, trade: dict, event_type: str, event_data: Dict[str, Any]):
        """Log a trade event"""
        symbol = trade.get("symbol", "unknown")
        trade_id = trade.get("trade_id") or self._generate_trade_id(symbol)
        
        self.lifecycle_logger.log_trade_event(
            trade_id=trade_id,
            symbol=symbol,
            event_type=event_type,
            event_data=event_data
        )

    async def start(self):
        """Start background tasks"""
        # Removed debounce_save task - now using immediate saves
        if self._sync_task is None:
            self._sync_task = asyncio.create_task(self.sync_with_broker())
        logger.info("TradeManager background tasks started")

    async def stop(self):
        """Stop background tasks"""
        # Removed debounce_save task - now using immediate saves
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            self._sync_task = None

        logger.info("TradeManager background tasks stopped")

    def load_trades(self):
        """Load trades from JSON file and apply validation/cleanup"""
        for attempt in range(3):
            try:
                if not os.path.exists(self.config_path):
                    logger.warning(f"No trade file found at {self.config_path}")
                    return []
                
                with open(self.config_path, "r") as f:
                    trades = json.load(f)
                
                # TradeManager ignores editing field entirely - only cares about order/trade status
                logger.info(f"TradeManager: Loaded {len(trades)} trades, ignoring editing field for evaluation")
                
                return trades
                
            except Exception as e:
                logger.error(f"Failed to load trades (attempt {attempt + 1}): {e}")
                if attempt < 2:
                    time.sleep(1)
        logger.error("Max retries reached for loading trades")
        return []
    
    def _get_fresh_trade_config(self, symbol: str) -> Optional[dict]:
        """
        Get fresh trade configuration for a symbol directly from saved_trades.json.
        This ensures we always have the latest trade status and configuration.
        """
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"No trade file found at {self.config_path}")
                return None
            
            with open(self.config_path, "r") as f:
                trades = json.load(f)
            
            # Find trade for the specific symbol
            for trade in trades:
                if trade.get("symbol") == symbol:
                    return trade
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to read fresh trade config for {symbol}: {e}")
            return None
    
    def _update_trade_in_file(self, symbol: str, updated_trade: dict):
        """
        Update a specific trade in saved_trades.json file.
        This replaces the old trade with the updated one.
        """
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"No trade file found at {self.config_path}")
                return False
            
            with open(self.config_path, "r") as f:
                trades = json.load(f)
            
            # Find and update the trade
            for i, trade in enumerate(trades):
                if trade.get("symbol") == symbol:
                    trades[i] = updated_trade
                    break
            else:
                logger.warning(f"Trade not found for symbol {symbol}")
                return False
            
            # Write back to file atomically
            with open(self.config_path + ".tmp", "w") as f:
                json.dump(trades, f, indent=2)
            os.replace(self.config_path + ".tmp", self.config_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update trade for {symbol}: {e}")
            return False
    
    def _get_trade_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Find trade by symbol in the main trades list"""
        for trade in self.trades:
            if trade.get("symbol") == symbol:
                return trade
        return None

    async def debounce_save(self):
        """Background task to save trades with debouncing"""
        while True:
            if self.save_pending:
                self._save_trades()
                self.save_pending = False
            await asyncio.sleep(self.save_delay)

    def _save_trades(self):
        """Save trades to JSON file"""
        logger.info(f"DEBUG: _save_trades() called - trades count: {len(self.trades)}")
        serializable_trades = []
        for i, trade in enumerate(self.trades):
            logger.info(f"DEBUG: Trade {i} - symbol: {trade.get('symbol')}, status: {trade.get('order_status')}")
            trade_copy = dict(trade)
            trade_copy.pop("contract", None)
            serializable_trades.append(trade_copy)
        try:
            logger.info(f"DEBUG: Writing to file: {self.config_path}")
            with open(self.config_path + ".tmp", "w") as f:
                json.dump(serializable_trades, f, indent=2)
            os.replace(self.config_path + ".tmp", self.config_path)
            logger.info("DEBUG: Trades saved to disk successfully")
        except Exception as e:
            logger.error(f"Failed to save trades: {e}")

    def save_trades(self):
        """Immediately save trades to JSON file"""
        self._save_trades()

    async def sync_with_broker(self):
        """Sync trade positions with broker using error handling"""
        try:
            # Check circuit breaker before attempting sync
            if not self.broker_circuit_breaker.can_execute():
                logger.warning("🚨 Broker circuit breaker OPEN - skipping sync")
                return
            
            # Use error handler for broker sync
            positions = await self.error_handler.execute_with_retry(
                "sync_positions_with_broker",
                self.adapter.get_positions
            )
            
            if positions:
                for pos in positions:
                    # Handle IB Position objects properly - they don't have .get() method
                    try:
                        # Extract symbol from Position object
                        symbol = pos.contract.symbol if hasattr(pos, 'contract') and hasattr(pos.contract, 'symbol') else None
                        
                        if symbol:
                            trade = self._get_fresh_trade_config(symbol)
                            if trade and trade.get("trade_status") in ["live", TradeStatus.LIVE.value]:
                                # Extract position data from IB Position object
                                filled_qty = pos.position if hasattr(pos, 'position') else 0
                                avg_price = pos.avgCost if hasattr(pos, 'avgCost') else 0
                                
                                trade["filled_qty"] = filled_qty
                                trade["executed_price"] = avg_price
                                logger.info(f"✅ Synced trade for {symbol} with broker position: {filled_qty} shares @ ${avg_price:.2f}")
                    except AttributeError as e:
                        logger.warning(f"⚠️ Could not extract position data: {e}")
                        continue
                
                # Record success for circuit breaker
                self.broker_circuit_breaker.record_success()
            
            self.save_trades()
            
        except Exception as e:
            logger.error(f"❌ Failed to sync with broker: {e}")
            self.broker_circuit_breaker.record_failure()
            # Log the error event
            self.lifecycle_logger.log_trade_event(
                "system",
                "SYSTEM",
                "broker_sync_error",
                {"error": str(e)}
            )

    async def preload_contracts(self, symbols: list[str]):
        """Preload contract details with error handling"""
        try:
            # Check circuit breaker before attempting preload
            if not self.market_data_circuit_breaker.can_execute():
                logger.warning("🚨 Market data circuit breaker OPEN - skipping contract preload")
                return
            
            # Use error handler for contract preload
            await self.error_handler.execute_with_retry(
                "preload_contracts",
                self._preload_contracts_internal,
                symbols
            )
            
            # Record success for circuit breaker
            self.market_data_circuit_breaker.record_success()
            
        except Exception as e:
            logger.error(f"❌ Failed to preload contracts: {e}")
            self.market_data_circuit_breaker.record_failure()
    
    async def _preload_contracts_internal(self, symbols: list[str]):
        """Internal contract preload with error handling"""
        for symbol in symbols:
            if symbol not in self.contract_details:
                try:
                    contract_details = await self.adapter.get_contract_details_batch([symbol])
                    if contract_details and symbol in contract_details:
                        self.contract_details[symbol] = contract_details[symbol]
                        logger.info(f"✅ Preloaded contract details for {symbol}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to preload contract for {symbol}: {e}")
                    continue
    
    async def preload_volatility(self, symbols: list[str], lookback: int = 30):
        """Preload volatility data with error handling"""
        try:
            # Check circuit breaker before attempting preload
            if not self.market_data_circuit_breaker.can_execute():
                logger.warning("🚨 Market data circuit breaker OPEN - skipping volatility preload")
                return
            
            # Use error handler for volatility preload
            await self.error_handler.execute_with_retry(
                "preload_volatility",
                self._preload_volatility_internal,
                symbols, lookback
            )
            
            # Record success for circuit breaker
            self.market_data_circuit_breaker.record_success()
            
        except Exception as e:
            logger.error(f"❌ Failed to preload volatility: {e}")
            self.market_data_circuit_breaker.record_failure()
    
    async def _preload_volatility_internal(self, symbols: list[str], lookback: int = 30):
        """Internal volatility preload with error handling"""
        if not self.md_client:
            logger.warning("⚠️ No market data client available for volatility preload")
            return
        
        for symbol in symbols:
            if symbol not in self.volatility_cache:
                try:
                    # Get historical data for volatility calculation
                    historical_data = await self.md_client.get_historical_data(
                        symbol, lookback, "1d"
                    )
                    
                    if historical_data and len(historical_data) >= lookback:
                        # Calculate volatility metrics
                        prices = [bar["close"] for bar in historical_data]
                        atr = calculate_atr(historical_data)
                        adr = calculate_adr(historical_data)
                        
                        self.volatility_cache[symbol] = {
                            "atr": atr,
                            "adr": adr,
                            "price_std": statistics.stdev(prices) if len(prices) > 1 else 0,
                            "last_updated": time.time()
                        }
                        logger.info(f"✅ Preloaded volatility for {symbol}: ATR={atr:.2f}, ADR={adr:.2f}")
                    else:
                        logger.warning(f"⚠️ Insufficient data for volatility calculation: {symbol}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to preload volatility for {symbol}: {e}")
                    continue

    async def evaluate_trade_on_tick(self, symbol: str, price: float, rolling_window=None):
        """
        Evaluate trade on incoming tick with comprehensive error handling.
        Always reads fresh trade config from saved_trades.json.
        """
        try:
            logger.info(f"DEBUG: evaluate_trade_on_tick called for {symbol} at ${price}")
            
            # Read fresh trade config from file - no caching
            trade = self._get_fresh_trade_config(symbol)
            if not trade:
                logger.info(f"DEBUG: No trade found for {symbol}")
                return
            
            logger.info(f"DEBUG: Found trade for {symbol} - status: {trade.get('order_status')} / {trade.get('trade_status')}")
            
            # Guard: Don't process trades in terminal states
            trade_status = trade.get("trade_status")
            order_status = trade.get("order_status")
            terminal_order_states = {"Cancelled", "Rejected", "Inactive"}
            terminal_trade_states = {"Closed", "Cancelled"}
            
            if trade_status in terminal_trade_states or order_status in terminal_order_states:
                logger.info(f"DEBUG: Skipping {symbol} - trade in terminal state (trade: {trade_status}, order: {order_status})")
                return
            
            # Check circuit breaker before proceeding
            if not self.broker_circuit_breaker.can_execute():
                logger.warning(f"🚨 Broker circuit breaker OPEN for {symbol} - skipping evaluation")
                return
            
            # Fetch historical data and create populated rolling window
            populated_rolling_window = None
            if self.md_client:
                try:
                    logger.info(f"DEBUG: Fetching historical data for {symbol}")
                    historical_data = await self.md_client.get_historical_data(symbol, 30)
                    if historical_data and len(historical_data) >= 21:
                        # Extract close prices (handle both dict and Bar object formats)
                        close_prices = []
                        for bar in historical_data:
                            if hasattr(bar, 'close'):
                                close_prices.append(bar.close)  # IB Bar object
                            elif isinstance(bar, dict) and 'close' in bar:
                                close_prices.append(bar['close'])  # Dict format
                            else:
                                logger.warning(f"Unknown bar format: {type(bar)}")
                        # Create populated rolling window
                        populated_rolling_window = build_preloaded_rolling_window(close_prices, 30)
                        # Add current tick to rolling window
                        populated_rolling_window.append(price)
                        logger.info(f"DEBUG: Created rolling window with {len(populated_rolling_window)} data points")
                    else:
                        logger.warning(f"⚠️ Insufficient historical data for {symbol}: got {len(historical_data) if historical_data else 0} bars")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to fetch historical data for {symbol}: {e}")
            else:
                logger.warning(f"⚠️ No market data client available for {symbol}")
            
            logger.info(f"DEBUG: Circuit breaker OK, calling _evaluate_trade_internal")
            
            # Use error handler for evaluation
            await self.error_handler.execute_with_retry(
                f"evaluate_trade_{symbol}",
                self._evaluate_trade_internal,
                trade, price, populated_rolling_window
            )
            
        except Exception as e:
            logger.error(f"❌ Critical error in evaluate_trade_on_tick for {symbol}: {e}")
            self.broker_circuit_breaker.record_failure()
            # Log the error event
            trade = self._get_trade_by_symbol(symbol)
            if trade:
                self.lifecycle_logger.log_trade_event(
                    trade.get("trade_id", "unknown"),
                    symbol,
                    "critical_error",
                    {"error": str(e), "price": price}
                )
    
    async def _evaluate_trade_internal(self, trade: dict, price: float, rolling_window=None):
        """Internal trade evaluation with error handling"""
        try:
            logger.info(f"DEBUG: _evaluate_trade_internal called for {trade.get('symbol')}")
            
            # Evaluate entry conditions
            await self._evaluate_entry_conditions(trade, price, rolling_window)
            
            # Evaluate child orders if trade is live
            if trade.get("trade_status") == TradeStatus.FILLED.value:
                logger.info(f"DEBUG: Trade is FILLED, evaluating child orders")
                logger.info(f"DEBUG: About to call _evaluate_child_orders")
                try:
                    await self._evaluate_child_orders(trade, price, rolling_window)
                    logger.info(f"DEBUG: Child order evaluation completed")
                except Exception as child_error:
                    logger.error(f"❌ Error in child order evaluation: {child_error}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                logger.info(f"DEBUG: Finished child order evaluation block")
            else:
                logger.info(f"DEBUG: Trade status is {trade.get('trade_status')}, not evaluating child orders")
                
        except Exception as e:
            logger.error(f"❌ Error in _evaluate_trade_internal: {e}")
            raise

    async def _evaluate_entry_conditions(self, trade: dict, price: float, rolling_window):
        """
        Evaluate entry conditions for parent order.
        """
        # Skip entry evaluation if trade is already filled
        if trade.get("trade_status") == TradeStatus.FILLED.value:
            logger.info(f"DEBUG: Skipping entry evaluation for {trade.get('symbol')} - trade already filled")
            return
            
        # Check portfolio filters first
        portfolio_data = self._get_portfolio_data(trade)
        if self.portfolio_evaluator.is_portfolio_filter_active(trade):
            allowed, portfolio_details = self.portfolio_evaluator.should_allow_trade(trade, portfolio_data)
            if not allowed:
                logger.warning(f"Portfolio filter blocked trade for {trade.get('symbol')}: {portfolio_details}")
                return

        # Evaluate entry conditions
        if self.entry_evaluator.should_trigger_entry(trade, price, rolling_window):
            logger.info(f"Entry conditions met for {trade.get('symbol')} at price {price:.2f}")
            
            # DEBUG: Log trade object before update
            logger.info(f"DEBUG: Before update - trade status: {trade.get('order_status')}")
            logger.info(f"DEBUG: Trade object ID: {id(trade)}")
            
            # Update status
            old_status = trade.get("order_status", OrderStatus.WORKING.value)
            new_status = OrderStatus.ENTRY_ORDER_SUBMITTED.value
            trade["order_status"] = new_status

            self._log_status_transition(
                trade=trade,
                from_status=old_status,
                to_status=new_status,
                trigger="entry_conditions_met",
                context={"price": price, "rolling_window_size": len(rolling_window.get_window()) if rolling_window else 0}
            )

            # Persist to disk
            logger.info("DEBUG: About to persist status change to disk")
            self._update_trade_in_file(trade.get("symbol"), trade)

            # ⚠️ Ensure in-memory copy is also updated
            for i, t in enumerate(self.trades):
                if t.get("symbol") == trade["symbol"]:
                    self.trades[i] = trade
                    break

            logger.info("DEBUG: Status change persisted to disk and memory successfully")

            
            # Place parent order
            if self.order_executor:
                order_result = await self.order_executor.place_market_order(
                    symbol=trade.get("symbol"),
                    qty=trade.get("calculated_quantity", 0),
                    side="BUY" if trade.get("direction", "Long") == "Long" else "SELL",
                    trade=trade
                )
                
                if order_result:
                    logger.info(f"Parent order placed for {trade.get('symbol')}: {order_result}")
                    self._log_trade_event(trade, "order_placed", order_result)
                else:
                    logger.error(f"Failed to place parent order for {trade.get('symbol')}")
                    # Reset status on failure
                    trade["order_status"] = old_status
                    self._log_status_transition(
                        trade=trade,
                        from_status=OrderStatus.ENTRY_ORDER_SUBMITTED.value,
                        to_status=old_status,
                        trigger="order_placement_failed",
                        context={"error": "Failed to place order"}
                    )

            self.save_trades()

    async def _evaluate_child_orders(self, trade: dict, price: float, rolling_window):
        """
        Evaluate child orders (stops, targets, trailing stops).
        """
        logger.info(f"DEBUG: Evaluating child orders for {trade.get('symbol')} at ${price}")
        
        # 1. Evaluate stop loss
        if self.stop_loss_evaluator.is_stop_active(trade):
            logger.info(f"DEBUG: Stop loss is active, checking trigger")
            stop_triggered, stop_details = self.stop_loss_evaluator.should_trigger_stop(trade, price, rolling_window)
            if stop_triggered:
                logger.info(f"DEBUG: Stop loss triggered: {stop_details}")
                await self._execute_stop_loss(trade, stop_details)
        else:
            logger.info(f"DEBUG: Stop loss not active")

        # 2. Evaluate take profit
        if self.take_profit_evaluator.is_take_profit_active(trade):
            logger.info(f"DEBUG: Take profit is active, checking trigger at ${price}")
            tp_triggered, tp_details = self.take_profit_evaluator.should_trigger_take_profit(trade, price)
            logger.info(f"DEBUG: Take profit triggered: {tp_triggered}, details: {tp_details}")
            if tp_triggered:
                logger.info(f"DEBUG: Executing take profit: {tp_details}")
                await self._execute_take_profit(trade, tp_details)
        else:
            logger.info(f"DEBUG: Take profit not active")

        # 3. Evaluate trailing stop updates
        if self.trailing_stop_evaluator.is_trailing_stop_active(trade):
            logger.info(f"DEBUG: Trailing stop is active, checking updates")
            should_update, trailing_details = self.trailing_stop_evaluator.should_update_trailing_stop(
                trade, price, rolling_window
            )
            if should_update:
                self.trailing_stop_evaluator.update_trailing_stop(trade, trailing_details["new_trailing_stop"])

            # Check if trailing stop should be triggered
            trailing_triggered, trailing_trigger_details = self.trailing_stop_evaluator.should_trigger_trailing_stop(trade, price)
            if trailing_triggered:
                await self._execute_trailing_stop(trade, trailing_trigger_details)

    async def _execute_stop_loss(self, trade: dict, stop_details: Dict[str, Any]):
        """Execute stop loss order"""
        logger.info(f"Executing stop loss for {trade.get('symbol')}")
        
        if self.order_executor:
            logger.info(f"Order executor available, attempting to place exit order")
            order_result = await self.order_executor.submit_exit_order(
                symbol=trade.get("symbol"),
                qty=trade.get("filled_qty", trade.get("calculated_quantity", 0)),
                side="SELL" if trade.get("direction", "Long") == "Long" else "BUY",
                trade=trade
            )
            
            logger.info(f"Exit order result: {order_result}")
            
            if order_result:
                trade["order_status"] = OrderStatus.CONTINGENT_ORDER_SUBMITTED.value
                logger.info(f"Stop loss order placed: {order_result}")
                self.save_trades()  # Save after status change
            else:
                logger.error(f"Failed to place stop loss order for {trade.get('symbol')} - order_result was None")
        else:
            logger.error("No order executor available for stop loss")

    async def _execute_take_profit(self, trade: dict, tp_details: Dict[str, Any]):
        """Execute take profit order"""
        logger.info(f"Executing take profit for {trade.get('symbol')}")
        
        # Use the filled quantity for exit (simple approach)
        exit_quantity = trade.get("filled_qty", trade.get("calculated_quantity", 0))
        
        if exit_quantity <= 0:
            logger.warning(f"Invalid exit quantity for take profit: {exit_quantity}")
            return
        
        logger.info(f"DEBUG: Placing take profit exit order for {exit_quantity} shares")
        
        if self.order_executor:
            order_result = await self.order_executor.submit_exit_order(
                symbol=trade.get("symbol"),
                qty=exit_quantity,
                side="SELL" if trade.get("direction", "Long") == "Long" else "BUY",
                trade=trade
            )
            
            if order_result:
                trade["order_status"] = OrderStatus.CONTINGENT_ORDER_SUBMITTED.value
                logger.info(f"Take profit order placed: {order_result}")
                self.save_trades()  # Save after status change
            else:
                logger.error(f"Failed to place take profit order for {trade.get('symbol')}")
        else:
            logger.warning("No order executor available for take profit")

    async def _execute_trailing_stop(self, trade: dict, trailing_details: Dict[str, Any]):
        """Execute trailing stop order"""
        logger.info(f"Executing trailing stop for {trade.get('symbol')}")
        
        if self.order_executor:
            order_result = await self.order_executor.submit_exit_order(
                symbol=trade.get("symbol"),
                qty=trade.get("filled_qty", trade.get("calculated_quantity", 0)),
                side="SELL" if trade.get("direction", "Long") == "Long" else "BUY",
                trade=trade
            )
            
            if order_result:
                trade["order_status"] = OrderStatus.CONTINGENT_ORDER_SUBMITTED.value
                logger.info(f"Trailing stop order placed: {order_result}")
                self.save_trades()  # Save after status change
            else:
                logger.error(f"Failed to place trailing stop order for {trade.get('symbol')}")

    def _get_portfolio_data(self, trade: dict) -> Dict[str, Any]:
        """Get portfolio data for evaluation"""
        # This would typically come from a portfolio service
        # For now, return basic data
        return {
            "available_buying_power": 100000,  # Mock data
            "portfolio_value": 100000,
            "current_price": trade.get("current_price", 0),
            "positions": {},
            "current_portfolio_loss": 0
        }

    async def mark_trade_filled(self, symbol: str, fill_price: float, filled_qty: int):
        """Mark trade as filled and initialize child orders"""
        trade = self._get_fresh_trade_config(symbol)
        if not trade:
            logger.warning(f"No trade found for symbol {symbol}")
            return

        # Log status transitions - use actual current status from fresh trade data
        old_order_status = trade.get("order_status")
        old_trade_status = trade.get("trade_status")
        
        # Update trade with fill information
        trade["filled_qty"] = filled_qty
        trade["executed_price"] = fill_price
        
        # Update status
        new_order_status = OrderStatus.CONTINGENT_ORDER_WORKING.value
        new_trade_status = TradeStatus.FILLED.value
        trade["order_status"] = new_order_status
        trade["trade_status"] = new_trade_status

        # Log order status transition
        self._log_status_transition(
            trade=trade,
            from_status=old_order_status,
            to_status=OrderStatus.CONTINGENT_ORDER_WORKING.value,
            trigger="entry_order_filled",
            context={"fill_price": fill_price, "filled_qty": filled_qty}
        )
        
        # Log trade status transition
        self._log_status_transition(
            trade=trade,
            from_status=old_trade_status,
            to_status=TradeStatus.FILLED.value,
            trigger="entry_order_filled",
            context={"fill_price": fill_price, "filled_qty": filled_qty}
        )

        # Trailing stop initialization is now handled in evaluate_trade_on_tick with populated rolling window
        logger.info(f"✅ Trailing stop will be initialized on next tick evaluation for {trade.get('symbol')}")


        logger.info(f"Trade filled for {symbol}: {filled_qty} @ {fill_price:.2f}")
        
        # Save updated trade back to file
        self._update_trade_in_file(symbol, trade)

    async def mark_trade_closed(self, symbol: str, exit_price: float, exit_qty: int):
        """Mark trade as closed"""
        trade = self._get_fresh_trade_config(symbol)
        if not trade:
            logger.warning(f"No trade found for symbol {symbol}")
            return

        # Log status transitions
        old_order_status = trade.get("order_status", OrderStatus.CONTINGENT_ORDER_WORKING.value)
        old_trade_status = trade.get("trade_status", TradeStatus.FILLED.value)
        
        # Update trade status
        new_order_status = OrderStatus.INACTIVE.value
        new_trade_status = TradeStatus.CLOSED.value
        trade["order_status"] = new_order_status
        trade["trade_status"] = new_trade_status
        trade["exit_price"] = exit_price
        trade["exit_qty"] = exit_qty

        # Calculate P&L
        entry_price = trade.get("executed_price", 0)
        pnl = 0
        if entry_price > 0:
            if trade.get("direction", "Long") == "Long":
                pnl = (exit_price - entry_price) * exit_qty
            else:
                pnl = (entry_price - exit_price) * exit_qty
            trade["realized_pnl"] = pnl

        # Log order status transition
        self._log_status_transition(
            trade=trade,
            from_status=old_order_status,
            to_status=OrderStatus.INACTIVE.value,
            trigger="exit_order_filled",
            context={"exit_price": exit_price, "exit_qty": exit_qty, "pnl": pnl}
        )
        
        # Log trade status transition
        self._log_status_transition(
            trade=trade,
            from_status=old_trade_status,
            to_status=TradeStatus.CLOSED.value,
            trigger="exit_order_filled",
            context={"exit_price": exit_price, "exit_qty": exit_qty, "pnl": pnl}
        )

        logger.info(f"Trade closed for {symbol}: {exit_qty} @ {exit_price:.2f}, P&L: {pnl:.2f}")
        
        # Save updated trade back to file
        self._update_trade_in_file(symbol, trade)

    def get_trade_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed trade information"""
        trade = self._get_fresh_trade_config(symbol)
        if not trade:
            return None

        return {
            "trade": trade,
            "entry_details": self.entry_evaluator.get_entry_details(trade),
            "stop_details": self.stop_loss_evaluator.get_stop_details(trade),
            "take_profit_details": self.take_profit_evaluator.get_take_profit_details(trade),
            "trailing_stop_details": self.trailing_stop_evaluator.get_trailing_stop_details(trade)
        }
