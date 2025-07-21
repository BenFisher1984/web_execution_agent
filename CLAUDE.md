# CLAUDE.md - Trading Platform Project Instructions

## PROJECT OVERVIEW
This is a sophisticated trading execution platform designed for serious retail traders. The system helps traders execute and manage risk while away from the market, focusing strictly on post-decision execution (entry through exit).

### Core Philosophy
- **Reliability over complexity** - Backend-driven validation ensures system integrity
- **Moderate sophistication** - Designed for serious retail traders, not hedge funds
- **Technology infrastructure** - Not a financial services platform

### Target Market
1. APAC traders trading US markets (time zone management)
2. Part-time retail traders who cannot watch markets real-time
3. Full-time traders who need discipline in execution

## CRITICAL ARCHITECTURAL PRINCIPLES

### 🚨 ABSOLUTE RULE: BROKER IS EXECUTION ONLY
**The trading engine is the sole authority for all order logic, state, and lifecycle.**
- Broker receives ONLY direct, immediate execution commands
- NO order staging, management, or OCO/OCA logic at broker level
- ALL contingent orders managed 100% internally until exact moment of execution
- Broker never sees virtual, bracket, or conditional order logic

### Parent/Child Framework
- **Parent Orders**: Entry orders (virtual until conditions met, then sent to broker)
- **Child Orders**: All contingent orders (stops, targets) managed virtually
- **OCA Logic**: One-cancels-all handled by engine, not broker
- **Virtual Management**: ALL orders calculated locally, sent to broker only when triggered

## CORE ARCHITECTURE

### Modular Evaluator Design
```
Trade Manager (Central Orchestrator)
├── Entry Evaluator (parent order triggers)
├── Stop Loss Evaluator (static & dynamic stops)
├── Take Profit Evaluator (multiple targets, partial exits)
├── Trailing Stop Evaluator (local calculations)
└── Portfolio Evaluator (risk management, filters)
```

### Rule Structure
**Format**: Primary Source | Condition | Secondary Source | Value
- **Rule Types**: Entry, Initial Stop, Trailing Stop, Take Profit (one per type per trade)
- **Examples**:
  - Entry: Price >= Custom (100)
  - Stop: Price <= EMA(8) (calculated)
  - Take Profit: Price >= TradingView Alert (set at alert time)

### Data Flow
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

## STATUS FRAMEWORK

### Order Status Options
1. **Draft** - Being created/edited, not activated
2. **Working** - Validated, monitoring for entry conditions
3. **Entry Order Submitted** - Entry order sent to broker, awaiting fill
4. **Contingent Order Submitted** - Exit order sent to broker, awaiting confirmation
5. **Contingent Order Working** - Exit order accepted by broker, now live
6. **Inactive** - Order cancelled (by user or modification)
7. **Cancelled** - Explicit user cancellation
8. **Rejected** - Broker rejected the order

### Trade Status Options
1. **-** (blank/null) - No live order, no market risk
2. **Pending** - Order validated and working, waiting for entry condition
3. **Filled** - Entry filled, trade is live, market risk present
4. **Closed** - All positions/orders closed, no market risk

## BROKER CONNECTION ARCHITECTURE

### Shared IB Adapter Implementation
- **Single Connection**: IB broker adapter and market data client share one IB Gateway connection
- **Client ID Management**: Single client ID (2) used across all IB operations
- **Connection Status**: ✅ Successfully resolved duplicate connection issues
- **Implementation**: Shared adapter pattern in `backend/app.py` with `get_market_data_client()` function

## TECHNICAL IMPLEMENTATION

### Data Model Requirements
- **Order Table**: orderId, tradeId, parentId, ocaGroup, type, status, action, quantity, price, stopPrice
- **Trade Table**: tradeId, status, symbol, strategy, created_at, updated_at
- **Parent/Child Relationships**: Child orders have parentId pointing to entry order
- **OCA Groups**: Child orders grouped for one-cancels-all logic

### Performance Considerations
- Cache recent price history (200-500 bars per symbol)
- Pre-compute common indicator periods
- Lazy load rare periods with caching
- Monitor evaluation times in production

## SAAS BUSINESS MODEL

### Pricing Tiers
1. **Freemium** - 1 strategy (FREE)
2. **Basic** - 3 strategies ($19.95/month)
3. **Gold** - 10 strategies ($29.95/month)
4. **Premium** - Unlimited strategies ($39.95/month)

### Customer Acquisition Strategy
- Partner with leading traders (Peter Brandt, Mark Minervini)
- Build templates matching their strategies
- Enable followers to implement strategies they subscribe to

### Third-Party Software Provider Model
- No customer funds handling
- No regulatory licenses needed
- Customers keep their own IBKR accounts
- Direct API integration via customer authorization

## CURRENT DEVELOPMENT STATUS

### ✅ Completed
- Trade lifecycle definition
- Status framework
- Parent/child architecture
- Modular evaluator design
- Enhanced individual evaluators
- Central trade manager orchestrator
- Shared IB adapter implementation
- Duplicate connection resolution

### 🔄 In Progress
- Data model implementation
- OCA logic refinement
- Virtual order management testing

### 📋 Next Steps
- Portfolio integration
- Database choice finalization
- TradingView alert flexibility
- Portfolio filter expansion

## CONSTRAINTS & BOUNDARIES

### In Scope
- Basic rule types (Entry, Stop, Trailing, Take Profit)
- TradingView alerts (one per trade)
- Portfolio filters (available buying power)
- Parent/child order management
- OCA/OCO logic
- Modular evaluator architecture

### Out of Scope (for now)
- Custom indicators as primary source
- Multiple TradingView alerts per trade
- Complex portfolio filters beyond available buying power
- Multiple rules of the same type per trade
- HFT or day trading functionality

## KEY FEATURES

### Solution Highlights
1. Sophisticated contingent order system (easy to use, no coding required)
2. Broker adapter model for multiple broker support
3. TradingView webhook integration for automation
4. Partial fills and OCO functionality
5. Portfolio and trade level filters
6. AI-powered catalyst scans (via gomoon.ai partnership)
7. Community-driven risk management scripts
8. Multiple execution methods (quick trader, order, chart, automated)

### What This Platform Is NOT
- Not suitable for day traders or HFT
- Not for developing trading strategies (backtesting, scans)
- Focus is strictly on post-decision execution

## DEVELOPMENT GUIDELINES

### Code Style
- Backend-driven validation (GUI is user-friendly but backend is source of truth)
- Comprehensive error handling with clear user notifications
- Modular architecture with single responsibility principle
- Performance-conscious design (not HFT level)

### Development Approach
**🎯 ROBUSTNESS OVER QUICK FIXES**: When identifying bugs or issues, always implement the robust solution that prevents the entire class of problems, not just the immediate symptom. Choose comprehensive fixes that strengthen system integrity over minimal patches.

### Testing Requirements
- Test each evaluator independently
- Comprehensive audit trails for all actions
- Virtual order management testing
- Connection stability testing

## REFERENCE DOCUMENTS
- `SESSION_CONTEXT_PROMPT.md` - Full project context
- `KEY_PRINCIPLE_BROKER_EXECUTION_ONLY.md` - Critical architectural rule
- `TO DO - Parent_child_framework.md` - Contingent order management
- `ExectionAgent_SaaS_proposal.docx` - Original business proposal

---

**Remember**: Always reference the broker execution principle at the start of any session. The broker is ONLY an execution endpoint - never for order management, staging, or contingent logic.