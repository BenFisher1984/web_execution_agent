import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.unified_rule_engine import UnifiedRuleEngine, Rule, RuleCondition, RuleType, ConditionType

def test_unified_rule_engine():
    """Test the unified rule engine with various rule types"""
    
    # Initialize the unified rule engine
    engine = UnifiedRuleEngine()
    
    print("🧪 Testing Unified Rule Engine...")
    
    # Test 1: Simple Entry Rule (Price Above)
    print("\n📊 Test 1: Entry Rule - Price Above $100")
    
    entry_rule = Rule(
        rule_id="entry_1",
        rule_type=RuleType.ENTRY,
        conditions=[
            RuleCondition(
                condition_type=ConditionType.PRICE_ABOVE,
                parameters={"value": 100.0}
            )
        ],
        execution_config={
            "quantity": 100,
            "order_type": "market"
        }
    )
    
    # Test market data
    market_data = {
        "current_price": 105.0,
        "prices": [100, 101, 102, 103, 104, 105]
    }
    
    import asyncio
    result = asyncio.run(engine.evaluate_rule(entry_rule, market_data))
    
    print(f"✅ Entry Rule Result: {result['triggered']}")
    print(f"   Details: {result['condition_results']}")
    
    # Test 2: Complex Entry Rule (EMA Crossover)
    print("\n📊 Test 2: Entry Rule - EMA Crossover")
    
    ema_entry_rule = Rule(
        rule_id="entry_2",
        rule_type=RuleType.ENTRY,
        conditions=[
            RuleCondition(
                condition_type=ConditionType.EMA_CROSSOVER,
                parameters={
                    "ema_fast": 8,
                    "ema_slow": 21,
                    "signal": "bullish"
                }
            )
        ],
        execution_config={
            "quantity": 50,
            "order_type": "market"
        }
    )
    
    # Test with price data that would create EMA crossover
    ema_market_data = {
        "current_price": 110.0,
        "prices": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120]
    }
    
    ema_result = asyncio.run(engine.evaluate_rule(ema_entry_rule, ema_market_data))
    print(f"✅ EMA Entry Rule Result: {ema_result['triggered']}")
    print(f"   Details: {ema_result['condition_results']}")
    
    # Test 3: Stop Loss Rule
    print("\n📊 Test 3: Stop Loss Rule - Price Below $90")
    
    stop_rule = Rule(
        rule_id="stop_1",
        rule_type=RuleType.INITIAL_STOP,
        conditions=[
            RuleCondition(
                condition_type=ConditionType.PRICE_BELOW,
                parameters={"value": 90.0}
            )
        ],
        execution_config={
            "quantity": 100,
            "order_type": "market"
        }
    )
    
    # Test with price below stop
    stop_market_data = {
        "current_price": 85.0,
        "prices": [100, 95, 90, 85]
    }
    
    stop_result = asyncio.run(engine.evaluate_rule(stop_rule, stop_market_data))
    print(f"✅ Stop Loss Rule Result: {stop_result['triggered']}")
    print(f"   Details: {stop_result['condition_results']}")
    
    # Test 4: Take Profit Rule
    print("\n📊 Test 4: Take Profit Rule - Price Above $115")
    
    tp_rule = Rule(
        rule_id="tp_1",
        rule_type=RuleType.TAKE_PROFIT,
        conditions=[
            RuleCondition(
                condition_type=ConditionType.PRICE_ABOVE,
                parameters={"value": 115.0}
            )
        ],
        execution_config={
            "quantity": 100,
            "order_type": "market"
        }
    )
    
    # Test with price above take profit
    tp_market_data = {
        "current_price": 120.0,
        "prices": [100, 105, 110, 115, 120]
    }
    
    tp_result = asyncio.run(engine.evaluate_rule(tp_rule, tp_market_data))
    print(f"✅ Take Profit Rule Result: {tp_result['triggered']}")
    print(f"   Details: {tp_result['condition_results']}")
    
    # Test 5: Complex Rule with Multiple Conditions
    print("\n📊 Test 5: Complex Rule - Price Above $100 AND EMA Above SMA")
    
    complex_rule = Rule(
        rule_id="complex_1",
        rule_type=RuleType.ENTRY,
        conditions=[
            RuleCondition(
                condition_type=ConditionType.PRICE_ABOVE,
                parameters={"value": 100.0},
                operator="AND",
                priority=1
            ),
            RuleCondition(
                condition_type=ConditionType.MOVING_AVERAGE_ABOVE,
                parameters={
                    "ma_config": {"type": "ema", "length": 8}
                },
                operator="AND",
                priority=2
            )
        ],
        execution_config={
            "quantity": 75,
            "order_type": "market"
        }
    )
    
    complex_market_data = {
        "current_price": 105.0,
        "prices": [100, 101, 102, 103, 104, 105, 106, 107, 108]
    }
    
    complex_result = asyncio.run(engine.evaluate_rule(complex_rule, complex_market_data))
    print(f"✅ Complex Rule Result: {complex_result['triggered']}")
    print(f"   Details: {complex_result['condition_results']}")
    
    # Test 6: Rule Management
    print("\n📊 Test 6: Rule Management")
    
    # Add rules to engine
    engine.add_rule(entry_rule)
    engine.add_rule(stop_rule)
    engine.add_rule(tp_rule)
    
    # Get rules by type
    entry_rules = engine.get_rules_by_type(RuleType.ENTRY)
    stop_rules = engine.get_rules_by_type(RuleType.INITIAL_STOP)
    
    print(f"✅ Entry Rules: {len(entry_rules)}")
    print(f"✅ Stop Rules: {len(stop_rules)}")
    print(f"✅ Total Rules: {len(engine.get_all_rules())}")
    
    # Test rule removal
    removed = engine.remove_rule("entry_1")
    print(f"✅ Rule Removal: {removed}")
    print(f"✅ Remaining Rules: {len(engine.get_all_rules())}")
    
    print("\n✅ All Unified Rule Engine tests completed!")

def test_rule_serialization():
    """Test rule serialization for storage/transmission"""
    
    print("\n🧪 Testing Rule Serialization...")
    
    # Create a rule
    rule = Rule(
        rule_id="test_rule",
        rule_type=RuleType.ENTRY,
        conditions=[
            RuleCondition(
                condition_type=ConditionType.PRICE_ABOVE,
                parameters={"value": 100.0}
            )
        ],
        execution_config={
            "quantity": 100,
            "order_type": "market"
        }
    )
    
    # Convert to dict (for JSON serialization)
    rule_dict = {
        "rule_id": rule.rule_id,
        "rule_type": rule.rule_type.value,
        "conditions": [
            {
                "condition_type": condition.condition_type.value,
                "parameters": condition.parameters,
                "operator": condition.operator,
                "priority": condition.priority
            }
            for condition in rule.conditions
        ],
        "execution_config": rule.execution_config,
        "enabled": rule.enabled
    }
    
    print(f"✅ Rule serialized to dict: {rule_dict}")
    
    # Reconstruct rule from dict
    reconstructed_rule = Rule(
        rule_id=rule_dict["rule_id"],
        rule_type=RuleType(rule_dict["rule_type"]),
        conditions=[
            RuleCondition(
                condition_type=ConditionType(condition["condition_type"]),
                parameters=condition["parameters"],
                operator=condition["operator"],
                priority=condition["priority"]
            )
            for condition in rule_dict["conditions"]
        ],
        execution_config=rule_dict["execution_config"],
        enabled=rule_dict["enabled"]
    )
    
    print(f"✅ Rule reconstructed: {reconstructed_rule.rule_id}")
    print(f"✅ Rule type: {reconstructed_rule.rule_type.value}")
    print(f"✅ Conditions: {len(reconstructed_rule.conditions)}")

if __name__ == "__main__":
    test_unified_rule_engine()
    test_rule_serialization() 