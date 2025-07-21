# Unified Data Model Design

## Design Principles

1. **Single Source of Truth**: One data format for both frontend and backend
2. **Type Safety**: Explicit types, no string parsing
3. **Extensibility**: Easy to add new indicators and parameters
4. **Validation**: Clear validation rules at both ends
5. **Performance**: Minimal overhead, no runtime parsing

## Core Data Model

### Rule Structure
```typescript
interface Rule {
  id: string;                    // Unique identifier
  enabled: boolean;              // Can be disabled without deletion
  condition: Condition;          // The comparison operation
  source: DataSource;            // What to compare
  target: DataTarget;            // What to compare against
}

interface Condition {
  operator: ">=" | "<=" | ">" | "<" | "==" | "!=";
  tolerance?: number;            // For fuzzy comparisons (optional)
}
```

### Data Sources (Left side of comparison)
```typescript
type DataSource = 
  | { type: "current_price" }
  | { type: "indicator", config: IndicatorConfig }

interface IndicatorConfig {
  indicator: "sma" | "ema" | "atr" | "adr" | "rsi" | "macd";
  period: number;
  source?: "open" | "high" | "low" | "close" | "volume";  // default: close
  offset?: number;               // bars ago (default: 0)
  
  // Indicator-specific parameters
  smoothing?: number;            // For EMA
  std_dev?: number;             // For Bollinger Bands
  fast_period?: number;         // For MACD
  slow_period?: number;         // For MACD
  signal_period?: number;       // For MACD
}
```

### Data Targets (Right side of comparison)
```typescript
type DataTarget = 
  | { type: "fixed_value", value: number }
  | { type: "indicator", config: IndicatorConfig }
  | { type: "current_price" }
  | { type: "entry_price" }
  | { type: "percentage_of", base: "entry_price" | "current_price", percentage: number }
```

## Complete Rule Examples

### Entry Rule Examples
```json
{
  "entry_rules": [
    {
      "id": "entry_001",
      "enabled": true,
      "condition": {
        "operator": ">="
      },
      "source": { "type": "current_price" },
      "target": { 
        "type": "fixed_value", 
        "value": 120 
      }
    }
  ]
}
```

### Stop Loss Rules
```json
{
  "stop_rules": [
    {
      "id": "stop_001", 
      "enabled": true,
      "condition": {
        "operator": "<="
      },
      "source": { "type": "current_price" },
      "target": {
        "type": "indicator",
        "config": {
          "indicator": "sma",
          "period": 21,
          "source": "close"
        }
      }
    }
  ]
}
```

### Trailing Stop Rules  
```json
{
  "trailing_stop_rules": [
    {
      "id": "trail_001",
      "enabled": true,
      "condition": {
        "operator": "<="  
      },
      "source": { "type": "current_price" },
      "target": {
        "type": "indicator",
        "config": {
          "indicator": "ema", 
          "period": 8,
          "source": "close",
          "offset": 0
        }
      }
    }
  ]
}
```

### Take Profit Rules
```json
{
  "take_profit_rules": [
    {
      "id": "tp_001",
      "enabled": true, 
      "condition": {
        "operator": ">="
      },
      "source": { "type": "current_price" },
      "target": {
        "type": "percentage_of",
        "base": "entry_price", 
        "percentage": 15.0
      }
    }
  ]
}
```

## Advanced Rule Examples

### Multiple Take Profit Levels
```json
{
  "take_profit_rules": [
    {
      "id": "tp_001",
      "enabled": true,
      "condition": { "operator": ">=" },
      "source": { "type": "current_price" },
      "target": { "type": "fixed_value", "value": 150 },
      "quantity_percentage": 50  // Exit 50% of position
    },
    {
      "id": "tp_002", 
      "enabled": true,
      "condition": { "operator": ">=" },
      "source": { "type": "current_price" },
      "target": { "type": "fixed_value", "value": 200 },
      "quantity_percentage": 100  // Exit remaining 50%
    }
  ]
}
```

### Complex Indicator Rules
```json
{
  "entry_rules": [
    {
      "id": "macd_crossover",
      "enabled": true,
      "condition": { "operator": ">" },
      "source": {
        "type": "indicator",
        "config": {
          "indicator": "macd",
          "fast_period": 12,
          "slow_period": 26,
          "signal_period": 9
        }
      },
      "target": {
        "type": "fixed_value",
        "value": 0
      }
    }
  ]
}
```

## Frontend Component Design

### Rule Builder Component Structure
```jsx
const RuleBuilder = ({ rule, onChange }) => {
  return (
    <div className="rule-builder">
      {/* Source Selection */}
      <DataSourceSelector 
        value={rule.source}
        onChange={(source) => onChange({...rule, source})}
      />
      
      {/* Condition Selection */}
      <ConditionSelector
        value={rule.condition} 
        onChange={(condition) => onChange({...rule, condition})}
      />
      
      {/* Target Selection */}
      <DataTargetSelector
        value={rule.target}
        onChange={(target) => onChange({...rule, target})}
      />
    </div>
  );
};
```

### Indicator Configuration Component
```jsx
const IndicatorConfig = ({ config, onChange }) => {
  return (
    <div className="indicator-config">
      <select 
        value={config.indicator}
        onChange={(e) => onChange({...config, indicator: e.target.value})}
      >
        <option value="sma">Simple Moving Average</option>
        <option value="ema">Exponential Moving Average</option>
        <option value="atr">Average True Range</option>
        <option value="rsi">Relative Strength Index</option>
      </select>
      
      <input
        type="number"
        placeholder="Period"
        value={config.period || ''}
        onChange={(e) => onChange({...config, period: parseInt(e.target.value)})}
      />
      
      {/* Conditional fields based on indicator type */}
      {config.indicator === 'ema' && (
        <input
          type="number" 
          placeholder="Smoothing"
          value={config.smoothing || ''}
          onChange={(e) => onChange({...config, smoothing: parseFloat(e.target.value)})}
        />
      )}
    </div>
  );
};
```

## Backend Evaluator Design

### Unified Rule Evaluator
```python
class RuleEvaluator:
    def __init__(self, market_data_client):
        self.md_client = market_data_client
        self.indicator_calculator = IndicatorCalculator()
    
    def evaluate_rule(self, rule: dict, current_price: float, rolling_window) -> bool:
        """Evaluate a single rule against current market data"""
        
        # Calculate source value
        source_value = self._calculate_data_source(
            rule["source"], current_price, rolling_window
        )
        
        # Calculate target value  
        target_value = self._calculate_data_target(
            rule["target"], current_price, rolling_window
        )
        
        # Apply condition
        return self._apply_condition(
            source_value, target_value, rule["condition"]
        )
    
    def _calculate_data_source(self, source: dict, current_price: float, rolling_window) -> float:
        if source["type"] == "current_price":
            return current_price
        elif source["type"] == "indicator":
            return self.indicator_calculator.calculate(
                source["config"], rolling_window
            )
        else:
            raise ValueError(f"Unknown source type: {source['type']}")
    
    def _calculate_data_target(self, target: dict, current_price: float, rolling_window) -> float:
        if target["type"] == "fixed_value":
            return target["value"]
        elif target["type"] == "current_price":
            return current_price
        elif target["type"] == "indicator":
            return self.indicator_calculator.calculate(
                target["config"], rolling_window
            )
        elif target["type"] == "percentage_of":
            base_value = self._get_base_value(target["base"])
            return base_value * (1 + target["percentage"] / 100)
        else:
            raise ValueError(f"Unknown target type: {target['type']}")
    
    def _apply_condition(self, source_value: float, target_value: float, condition: dict) -> bool:
        operator = condition["operator"]
        tolerance = condition.get("tolerance", 0)
        
        if operator == ">=":
            return source_value >= (target_value - tolerance)
        elif operator == "<=":
            return source_value <= (target_value + tolerance)
        elif operator == ">":
            return source_value > target_value
        elif operator == "<":
            return source_value < target_value
        elif operator == "==":
            return abs(source_value - target_value) <= tolerance
        elif operator == "!=":
            return abs(source_value - target_value) > tolerance
        else:
            raise ValueError(f"Unknown operator: {operator}")
```

### Indicator Calculator
```python
class IndicatorCalculator:
    def calculate(self, config: dict, rolling_window) -> float:
        indicator_type = config["indicator"]
        period = config["period"]
        source = config.get("source", "close")
        offset = config.get("offset", 0)
        
        # Get price data
        prices = self._extract_prices(rolling_window, source)
        
        # Apply offset
        if offset > 0:
            prices = prices[:-offset]
        
        # Calculate indicator
        if indicator_type == "sma":
            return calculate_sma(prices, period)
        elif indicator_type == "ema":
            smoothing = config.get("smoothing", 2)
            return calculate_ema(prices, period, smoothing)
        elif indicator_type == "atr":
            return calculate_atr(rolling_window.get_bars(), period)
        elif indicator_type == "rsi":
            return calculate_rsi(prices, period)
        elif indicator_type == "macd":
            fast = config.get("fast_period", 12)
            slow = config.get("slow_period", 26)
            signal = config.get("signal_period", 9)
            return calculate_macd(prices, fast, slow, signal)
        else:
            raise ValueError(f"Unknown indicator: {indicator_type}")
```

## Migration Strategy

### Phase 1: Data Model Implementation
1. **Define TypeScript interfaces** for frontend type safety
2. **Implement unified rule structure** in saved_trades.json
3. **Create RuleEvaluator class** for backend processing
4. **Build IndicatorCalculator** for all technical indicators

### Phase 2: Frontend Rebuild
1. **Create new rule builder components** using unified model
2. **Implement data validation** on form submission
3. **Add rule preview/testing** functionality
4. **Migrate existing trade data** to new format

### Phase 3: Backend Integration
1. **Replace all existing evaluators** with unified RuleEvaluator
2. **Implement comprehensive testing** for all rule combinations
3. **Add performance optimization** for indicator calculations
4. **Create rule debugging** and monitoring tools

## Benefits of This Design

### 1. Type Safety
- No string parsing or runtime interpretation
- Clear validation at compile/runtime
- Explicit data contracts

### 2. Extensibility  
- New indicators require only adding to IndicatorCalculator
- New rule types just extend the DataSource/DataTarget unions
- No changes to UI or evaluation logic

### 3. Performance
- Pre-calculated indicators stored in rolling window
- No repeated parsing or interpretation
- Efficient condition evaluation

### 4. Maintainability
- Single evaluation engine for all rule types
- Clear separation of concerns
- Easy to test and debug

### 5. User Experience
- Rich rule building interface
- Real-time validation and preview
- Complex strategies possible

## Validation Rules

### Frontend Validation
```typescript
const validateRule = (rule: Rule): string[] => {
  const errors: string[] = [];
  
  if (!rule.id) errors.push("Rule ID is required");
  if (!rule.condition?.operator) errors.push("Condition operator is required");
  if (!rule.source) errors.push("Source is required");
  if (!rule.target) errors.push("Target is required");
  
  // Validate indicator configs
  if (rule.source.type === "indicator") {
    errors.push(...validateIndicatorConfig(rule.source.config));
  }
  if (rule.target.type === "indicator") {
    errors.push(...validateIndicatorConfig(rule.target.config));
  }
  
  return errors;
};
```

### Backend Validation
```python
def validate_rule(rule: dict) -> List[str]:
    errors = []
    
    if "id" not in rule:
        errors.append("Rule ID is required")
    if "condition" not in rule or "operator" not in rule["condition"]:
        errors.append("Condition operator is required")
    if "source" not in rule:
        errors.append("Source is required")
    if "target" not in rule:
        errors.append("Target is required")
    
    return errors
```

---

This unified data model eliminates all current data contract mismatches and provides a professional, extensible foundation for the trading system.