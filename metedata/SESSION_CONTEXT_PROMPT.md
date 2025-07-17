# SESSION CONTEXT PROMPT
*Use this prompt to restore full project context in new sessions*

---

## PROJECT OVERVIEW
**Trading Platform for Serious Retail Traders**
- **Target**: Serious retail traders (not hedge funds)
- **Philosophy**: Reliability over complexity, backend-driven validation
- **Complexity**: Moderate sophistication, not HFT-level complexity

---

## CORE ARCHITECTURE

### **Modular Evaluator Design**
- **Entry Evaluator**: Handles entry conditions (parent orders)
- **Stop Loss Evaluator**: Manages stop loss logic and dynamic stops
- **Take Profit Evaluator**: Handles take profit targets and partial exits
- **Trailing Stop Evaluator**: Manages trailing stop calculations and updates
- **Portfolio Evaluator**: Handles portfolio filters and risk management
- **Trade Manager**: Central orchestrator coordinating all evaluators

### **Rule Structure**
- **Rule Structure**: Primary Source | Condition | Secondary Source | Value
- **Rule Types**: Entry, Initial Stop, Trailing Stop, Take Profit (one per type per trade)
- **Validation**: Backend-driven, GUI provides user-friendly validation but backend is source of truth
- **Examples**:
  - Entry: Price >= Custom (100)
  - Stop: Price <= EMA(8) (calculated)
  - Take Profit: Price >= TradingView Alert (set at alert time)

### **Parent/Child Order Framework**
- **Parent Orders**: Entry orders are virtual until conditions are met, then sent to broker
- **Child Orders**: All contingent orders (stops, targets) are virtual until conditions are met, then sent to broker
- **OCA Logic**: One-cancels-all grouping managed by engine, not broker
- **Virtual Management**: ALL orders calculated locally, only sent to broker when conditions are triggered
- **Engine vs Broker**: Clear delineation - engine manages ALL virtual orders, broker only sees explicitly transmitted orders when conditions are met

---

## TRADE LIFECYCLE & STATUS FRAMEWORK

### **Order Status Options**
1. **Draft** - Being created/edited, not yet activated
2. **Working** - Validated, monitoring for entry conditions
3. **Entry Order Submitted** - Entry order sent to broker, awaiting fill
4. **Contingent Order Submitted** - Contingent/exit order sent to broker, awaiting confirmation
5. **Contingent Order Working** - Contingent order accepted by broker, now live
6. **Inactive** - Order cancelled (by user or modification)
7. **Cancelled** - Explicit user cancellation
8. **Rejected** - Broker rejected the order

### **Trade Status Options**
1. **-** (blank/null) - No live order, no market risk
2. **Pending** - Order validated and working, waiting for entry condition and/or broker fill
3. **Filled** - Entry filled, trade is live, market risk present
4. **Closed** - All positions/orders closed, no market risk

### **Status Transitions**
- All status changes are backend-driven and readonly in UI
- Only "Activate" action triggers backend validation
- If validation fails: Status unchanged, user notified
- If validation passes: Order becomes "Working", Trade becomes "Pending"

---

## ENGINE ARCHITECTURE

### **Central Orchestrator**
- **Trade Manager**: Main coordinator for all trade lifecycle management
- **Responsibilities**: 
  - Load/save trades to JSON
  - Evaluate trades on ticks
  - Manage trade status transitions
  - Sync with broker positions
  - Coordinate all evaluators

### **Individual Evaluators**
- **Entry Evaluator**: 
  - Evaluates entry conditions (parent order triggers)
  - Supports rule-based conditions (EMA crossover, moving averages, price levels)
  - Handles direction-specific logic (Long/Short)
- **Stop Loss Evaluator**:
  - Manages static and dynamic stops
  - Calculates active stops (static vs dynamic)
  - Handles OCA logic for stop orders
- **Take Profit Evaluator**:
  - Supports multiple target levels
  - Handles partial exits
  - Manages target priority (primary vs secondary)
- **Trailing Stop Evaluator**:
  - Calculates trailing stops locally
  - Updates trailing stops based on price movement
  - Only sends to broker when triggered
- **Portfolio Evaluator**:
  - Evaluates portfolio filters
  - Checks risk conditions
  - Manages position limits

### **Data Flow**
```
TickHandler → TradeManager
                ↓
            EntryEvaluator (parent order)
                ↓
            StopLossEvaluator (child orders)
            TakeProfitEvaluator (child orders)
            TrailingStopEvaluator (child orders)
                ↓
            OrderExecutor (places orders)
                ↓
            TradeManager (updates status)
```

---

## KEY DESIGN PRINCIPLES

### **Reliability First**
- Backend-driven validation prevents invalid states
- Comprehensive audit trails for all actions
- Error handling with clear user notifications
- System can never be in a state where an order is activated but cannot be evaluated

### **Modular Architecture**
- **Single Responsibility**: Each evaluator has one clear job
- **Easy Maintenance**: Debug and modify individual components
- **Independent Testing**: Test each evaluator separately
- **Clear Ownership**: No confusion about which component handles what

### **Moderate Complexity**
- Designed for serious retail traders, not hedge funds
- Single rule per type per trade (prevents complexity explosion)
- Performance-conscious design (not HFT)
- Extensible framework for future growth

### **User Experience**
- Clean, intuitive interface
- Clear status visibility
- Transparent workflow (Save → Activate → Monitor)
- Strategy persistence via dropdown

---

## TECHNICAL IMPLEMENTATION

### **Data Model Requirements**
- **Order Table**: orderId, tradeId, parentId, ocaGroup, type, status, action, quantity, price, stopPrice
- **Trade Table**: tradeId, status, symbol, strategy, created_at, updated_at
- **Parent/Child Relationships**: Child orders have parentId pointing to entry order
- **OCA Groups**: Child orders grouped for one-cancels-all logic

### **Performance Considerations**
- Cache recent price history (200-500 bars per symbol)
- Pre-compute common indicator periods
- Lazy load rare periods with caching
- Monitor evaluation times in production

### **Logging/Audit**
- Log all rule evaluations that result in action
- Log all TradingView alerts received
- Store in database (SQLite/Postgres) or structured log file
- Include: timestamp, trade ID, rule type, rule details, evaluation result, alert value

---

## BROKER CONNECTION ARCHITECTURE

### **Shared IB Adapter Implementation**
- **Single Connection**: IB broker adapter and market data client share one IB Gateway connection
- **Client ID Management**: Single client ID (2) used across all IB operations
- **Connection Status**: ✅ Successfully resolved duplicate connection issues
- **Implementation**: Shared adapter pattern in `backend/app.py` with `get_market_data_client()` function

### **Connection Flow**
```
Application Startup
        ↓
    IB Gateway Connection (clientId: 2)
        ↓
    Shared by:
    - IB Broker Adapter (execution)
    - IB Market Data Client (data)
        ↓
    Single Connection Pool
```

### **Benefits Achieved**
- **No Duplicate Connections**: Eliminated client ID conflicts
- **Resource Efficiency**: Single connection reduces overhead
- **Reliability**: Consistent connection state across components
- **Scalability**: Pattern supports additional IB operations

---

## CURRENT DEVELOPMENT PHASE
- **Completed**: 
  - Trade lifecycle definition
  - Status framework
  - Parent/child architecture
  - Modular evaluator design
  - Enhanced individual evaluators
  - Central trade manager orchestrator
  - ✅ Shared IB adapter implementation
  - ✅ Duplicate connection resolution
- **Next Steps**: 
  - Data model implementation
  - OCA logic refinement
  - Virtual order management testing
  - Portfolio integration
- **Open Questions**: 
  - Database choice
  - Portfolio filter expansion
  - TradingView alert flexibility

---

## CONSTRAINTS & BOUNDARIES

### **In Scope**
- Basic rule types (Entry, Stop, Trailing, Take Profit)
- TradingView alerts (one per trade)
- Portfolio filters (available buying power)
- Parent/child order management
- OCA/OCO logic
- Modular evaluator architecture

### **Out of Scope (for now)**
- Custom indicators as primary source
- Multiple TradingView alerts per trade
- Complex portfolio filters beyond available buying power
- Multiple rules of the same type per trade
- Complex unified rule engines

---

## REFERENCE DOCUMENTS
- `DESIGN_PRINCIPLES.md` - Core philosophy and standards
- `STRATEGY_RULE_ENGINE_DESIGN.md` - Technical architecture
- `TRADE_LIFE_CYCLE.md` - Status transitions and workflow
- `TO DO - Parent_child_framework.md` - Contingent order management

---

**Use this prompt at the start of new sessions to restore full project context and maintain consistency across development phases.** 