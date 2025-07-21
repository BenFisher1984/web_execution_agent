# Data Model Standardization Plan

## Problem Statement

The trading platform has a **critical data model inconsistency** between frontend and backend:

- **Frontend**: Saves indicator rules as strings (`"secondary_source": "SMA 21"`)
- **Backend**: Expects structured objects (`{"indicator": "sma", "parameters": {"lookback": 21}}`)

This mismatch causes:
- Parsing errors in evaluators
- "Unsupported trailing stop indicator: None" warnings
- Dynamic indicator calculations failing
- Inconsistent data contracts across the system

## Current State Analysis

### Frontend Rule Format (Current)
```json
{
  "trailing_stop_rules": [{
    "primary_source": "Price",
    "condition": "<=", 
    "secondary_source": "SMA 21",
    "value": 102.57
  }]
}
```

### Backend Expected Format (Current)
```python
# Evaluators expect:
indicator = rule.get("indicator")           # None (missing)
params = rule.get("parameters", {})         # {} (empty)
lookback = params.get("lookback", 20)       # 20 (default)
```

### Root Cause
No parsing layer exists to convert `"SMA 21"` → `{"indicator": "sma", "parameters": {"lookback": 21}}`

## Solution Options

### Option 1: Add Parsing Layer (Quick Fix)
**Pros**: Minimal breaking changes, fastest implementation
**Cons**: Technical debt, error-prone string parsing, not professional

### Option 2: Standardize to Structured Format (Professional)
**Pros**: Type-safe, scalable, eliminates parsing, professional approach
**Cons**: Major breaking changes, significant refactoring required

### Option 3: Hybrid Approach (Recommended)
**Pros**: Gradual migration, supports both formats during transition
**Cons**: Temporary complexity, requires careful sequencing

## Recommended Approach: Hybrid Migration

### Phase 1: Backend Compatibility Layer (Week 1)
1. **Create parsing utility** to handle both formats
2. **Update all evaluators** to use the parsing utility
3. **Maintain backward compatibility** with existing string format
4. **Add comprehensive tests** for both data formats

### Phase 2: Frontend Standardization (Week 2)
1. **Design new structured format** for rule configuration
2. **Update rule panels** to save structured data
3. **Implement data migration** for existing trades
4. **Add validation** for new structured format

### Phase 3: Backend Modernization (Week 3)
1. **Remove parsing layer** once frontend migration is complete
2. **Simplify evaluator logic** to consume structured data directly
3. **Update all tests** to use new format
4. **Remove legacy string format support**

## Detailed Implementation Plan

### Phase 1: Backend Compatibility Layer

#### 1.1 Create Indicator Parser Utility
**File**: `backend/engine/utils/indicator_parser.py`

```python
def parse_indicator(rule: dict) -> dict:
    """
    Parse indicator from rule, supporting both formats:
    - Legacy: {"secondary_source": "SMA 21"}
    - New: {"indicator": {"type": "sma", "period": 21}}
    """
    # Check for new structured format first
    if "indicator" in rule:
        return rule["indicator"]
    
    # Parse legacy string format
    secondary_source = rule.get("secondary_source", "")
    if isinstance(secondary_source, str):
        return parse_indicator_string(secondary_source)
    
    return None

def parse_indicator_string(indicator_str: str) -> dict:
    """Parse strings like 'SMA 21', 'EMA 8', 'ATR', 'Custom'"""
    if not indicator_str or indicator_str == "Custom":
        return None
    
    parts = indicator_str.strip().split()
    if len(parts) == 2:
        indicator_type = parts[0].lower()  # 'sma', 'ema'
        period = int(parts[1])             # 21, 8
        return {"type": indicator_type, "period": period}
    elif len(parts) == 1:
        # Single indicators like 'ATR', 'ADR'
        return {"type": parts[0].lower(), "period": 14}  # default period
    
    return None
```

#### 1.2 Update All Evaluators
**Files to modify**:
- `entry_evaluator.py`
- `stop_loss_evaluator.py` 
- `trailing_stop_evaluator.py`
- `take_profit_evaluator.py`

**Pattern for each evaluator**:
```python
from backend.engine.utils.indicator_parser import parse_indicator

def _calculate_dynamic_value(self, rule: dict, rolling_window) -> float:
    # New parsing logic
    indicator_config = parse_indicator(rule)
    if not indicator_config:
        return None
    
    indicator_type = indicator_config["type"]
    period = indicator_config["period"]
    
    # Rest of calculation logic...
```

#### 1.3 Add Comprehensive Tests
**File**: `backend/tests/test_indicator_parser.py`

Test cases for:
- Legacy string format: "SMA 21", "EMA 8", "ATR"
- New structured format: `{"type": "sma", "period": 21}`
- Edge cases: empty strings, malformed data
- All evaluators with both formats

### Phase 2: Frontend Standardization

#### 2.1 Design New Rule Structure
**New structured format**:
```json
{
  "trailing_stop_rules": [{
    "primary_source": "Price",
    "condition": "<=",
    "secondary_source": {
      "type": "indicator",
      "indicator": {
        "type": "sma",
        "period": 21
      }
    },
    "value": null
  }]
}
```

#### 2.2 Update Rule Panels
**Files to modify**:
- `EntryRulesPanel.js`
- `StopRulesPanel.js`
- `TakeProfitRulesPanel.js`
- `TrailingStopRulesPanel.js`

**New component structure**:
```javascript
// Separate dropdowns for indicator type and period
<select name="indicator_type">
  <option value="sma">SMA</option>
  <option value="ema">EMA</option>
  <option value="atr">ATR</option>
</select>

<input type="number" name="indicator_period" placeholder="Period" />
```

#### 2.3 Data Migration Script
**File**: `backend/scripts/migrate_rule_format.py`

```python
def migrate_trade_rules(trade_file_path: str):
    """Migrate existing trades from string to structured format"""
    with open(trade_file_path, 'r') as f:
        trades = json.load(f)
    
    for trade in trades:
        for rule_type in ['entry_rules', 'initial_stop_rules', 
                         'trailing_stop_rules', 'take_profit_rules']:
            rules = trade.get(rule_type, [])
            for rule in rules:
                migrate_single_rule(rule)
    
    # Backup original file
    backup_path = f"{trade_file_path}.backup"
    shutil.copy2(trade_file_path, backup_path)
    
    # Save migrated data
    with open(trade_file_path, 'w') as f:
        json.dump(trades, f, indent=2)
```

### Phase 3: Backend Modernization

#### 3.1 Remove Parsing Layer
- Delete `indicator_parser.py`
- Simplify evaluator logic to consume structured data directly
- Remove legacy format support

#### 3.2 Update All Tests
- Convert test data to new structured format
- Remove parsing layer tests
- Add validation tests for structured format

## Risk Assessment

### High Risk Areas
1. **Data Loss**: Existing saved trades could become invalid
2. **Frontend Breakage**: Rule panels might not load correctly
3. **Evaluator Failures**: Dynamic indicators might stop working
4. **Test Failures**: Existing tests use legacy format

### Mitigation Strategies
1. **Comprehensive Backups**: Backup all trade files before migration
2. **Gradual Rollout**: Implement in phases with testing at each step
3. **Rollback Plan**: Keep legacy parsing code until migration is verified
4. **Extensive Testing**: Test both formats during transition period

## Success Criteria

### Phase 1 Complete When:
- [ ] All evaluators handle both string and structured formats
- [ ] Parsing utility has 100% test coverage
- [ ] No "Unsupported indicator" warnings in logs
- [ ] Dynamic indicators calculate correctly

### Phase 2 Complete When:
- [ ] Frontend saves structured indicator data
- [ ] All existing trades migrated successfully
- [ ] Rule panels work with new format
- [ ] Data validation prevents malformed rules

### Phase 3 Complete When:
- [ ] Legacy string format support removed
- [ ] All tests use structured format
- [ ] System performance improved (no parsing overhead)
- [ ] Code is cleaner and more maintainable

## Timeline

- **Week 1**: Backend compatibility layer implementation
- **Week 2**: Frontend standardization and migration
- **Week 3**: Backend modernization and cleanup
- **Week 4**: Testing, validation, and documentation

## Dependencies

### Technical Dependencies
- Node.js/React for frontend changes
- Python for backend parsing logic
- Test framework for comprehensive testing

### Business Dependencies
- User acceptance of brief downtime during migration
- Coordination with any external integrations
- Documentation updates for API consumers

## Rollback Plan

If migration fails:
1. **Restore backup files** of original trade data
2. **Revert frontend changes** to previous rule panel version
3. **Keep parsing layer** as permanent solution
4. **Document lessons learned** for future data model changes

---

**Next Steps**: Review and approve this plan before beginning Phase 1 implementation.