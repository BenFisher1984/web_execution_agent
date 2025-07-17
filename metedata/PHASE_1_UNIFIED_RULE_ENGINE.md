# Phase 1: Unified Rule Engine Structure

## 🎯 **What Phase 1 Requires**

### **Current State vs. Target State**

#### **❌ Current Architecture (Separate Evaluators)**
```
EntryEvaluator → handles entry conditions
StopLossEvaluator → handles stop losses  
TakeProfitEvaluator → handles take profits
StrategyEvaluator → handles complex strategies
```

#### **✅ Target Architecture (Unified Rule Engine)**
```
UnifiedRuleEngine → handles ALL rule types
├── Entry Rules
├── Stop Loss Rules  
├── Take Profit Rules
├── Trailing Stop Rules
├── Portfolio Filter Rules
└── Risk Condition Rules
```

## 🔧 **Phase 1 Implementation Requirements**

### **1. Core Components Required**

#### **A. Unified Rule Engine (`unified_rule_engine.py`)**
- ✅ **COMPLETED**: Single engine that handles all rule types
- ✅ **COMPLETED**: Dynamic condition evaluation
- ✅ **COMPLETED**: Rule management (add/remove/get)
- ✅ **COMPLETED**: Condition logic (AND/OR operators)

#### **B. Rule Types Enum**
```python
class RuleType(Enum):
    ENTRY = "entry"
    INITIAL_STOP = "initial_stop"
    TRAILING_STOP = "trailing_stop"
    TAKE_PROFIT = "take_profit"
    PORTFOLIO_FILTER = "portfolio_filter"
    RISK_CONDITION = "risk_condition"
```

#### **C. Condition Types Enum**
```python
class ConditionType(Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    EMA_CROSSOVER = "ema_crossover"
    MOVING_AVERAGE_ABOVE = "moving_average_above"
    MOVING_AVERAGE_BELOW = "moving_average_below"
    ADR_BELOW = "adr_below"
    # ... extensible for future conditions
```

### **2. Data Structures Required**

#### **A. RuleCondition**
```python
@dataclass
class RuleCondition:
    condition_type: ConditionType
    parameters: Dict[str, Any]
    operator: str = "AND"  # AND, OR
    priority: int = 1
```

#### **B. Rule**
```python
@dataclass
class Rule:
    rule_id: str
    rule_type: RuleType
    conditions: List[RuleCondition]
    execution_config: Dict[str, Any]
    enabled: bool = True
    created_at: datetime = None
    updated_at: datetime = None
```

### **3. Integration Requirements**

#### **A. Trade Manager Integration**
```python
# Replace separate evaluators with unified engine
class TradeManager:
    def __init__(self):
        self.unified_rule_engine = UnifiedRuleEngine()
        # Remove: self.entry_evaluator, self.stop_loss_evaluator, etc.
    
    async def evaluate_trade_on_tick(self, trade, price, rolling_window):
        # Use unified engine for all evaluations
        rule = self.convert_trade_to_rule(trade)
        result = await self.unified_rule_engine.evaluate_rule(rule, market_data)
        return result
```

#### **B. API Integration**
```python
# New API endpoints for rule management
@app.post("/rules")
async def create_rule(rule_data: dict):
    rule = Rule.from_dict(rule_data)
    engine.add_rule(rule)
    return {"status": "success", "rule_id": rule.rule_id}

@app.get("/rules/{rule_type}")
async def get_rules_by_type(rule_type: str):
    rules = engine.get_rules_by_type(RuleType(rule_type))
    return {"rules": [rule.to_dict() for rule in rules]}
```

## 🚀 **Benefits of Phase 1**

### **1. Scalability**
- **Easy to add new rule types**: Just add to `RuleType` enum
- **Easy to add new conditions**: Just add to `ConditionType` enum
- **No code changes needed**: All logic is configuration-driven

### **2. Consistency**
- **Single evaluation logic**: All rules use the same engine
- **Unified error handling**: Consistent error reporting
- **Standardized results**: All evaluations return the same format

### **3. Flexibility**
- **Complex condition logic**: AND/OR operators between conditions
- **Priority system**: Conditions can have priorities
- **Dynamic configuration**: Rules can be enabled/disabled

### **4. Maintainability**
- **Single codebase**: One engine instead of multiple evaluators
- **Clear separation**: Rules vs. evaluation logic
- **Easy testing**: Test one engine instead of multiple evaluators

## 📋 **Phase 1 Checklist**

### **✅ Completed**
- [x] Unified Rule Engine implementation
- [x] Rule and Condition data structures
- [x] Basic condition evaluators (price, EMA, moving averages)
- [x] Rule management (add/remove/get)
- [x] Condition logic (AND/OR)
- [x] Comprehensive testing

### **🔄 In Progress**
- [ ] Integration with TradeManager
- [ ] API endpoints for rule management
- [ ] Migration from separate evaluators
- [ ] Frontend integration

### **⏳ Next Steps**
- [ ] Advanced condition evaluators (volume, volatility, time-based)
- [ ] Portfolio-level rule evaluation
- [ ] Rule persistence and loading
- [ ] Performance optimization

## 💡 **Example Usage**

### **Creating a Complex Rule**
```python
# Entry rule: Buy when price > $100 AND EMA crossover bullish
entry_rule = Rule(
    rule_id="entry_1",
    rule_type=RuleType.ENTRY,
    conditions=[
        RuleCondition(
            condition_type=ConditionType.PRICE_ABOVE,
            parameters={"value": 100.0},
            operator="AND"
        ),
        RuleCondition(
            condition_type=ConditionType.EMA_CROSSOVER,
            parameters={
                "ema_fast": 8,
                "ema_slow": 21,
                "signal": "bullish"
            },
            operator="AND"
        )
    ],
    execution_config={
        "quantity": 100,
        "order_type": "market"
    }
)

# Add to engine
engine.add_rule(entry_rule)

# Evaluate on market data
result = await engine.evaluate_rule(entry_rule, market_data)
```

## 🎯 **What This Enables**

### **1. GUI-Driven Strategy Creation**
Users can create complex strategies through the frontend without touching code:
- Entry rules with multiple conditions
- Dynamic stop loss rules
- Trailing stop rules
- Portfolio-level risk rules

### **2. Real-time Strategy Evaluation**
Every price tick evaluates all active rules:
- Automatic entry/exit decisions
- Risk management enforcement
- Portfolio balance maintenance

### **3. Extensible Framework**
Easy to add new capabilities:
- New technical indicators
- New risk metrics
- New order types
- New market conditions

This unified approach transforms your system from a collection of separate evaluators into a single, powerful, and flexible rule engine that can handle any trading strategy your users can imagine! 