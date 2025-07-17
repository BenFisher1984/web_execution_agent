import pytest
from backend.engine.entry_evaluator import EntryEvaluator

@pytest.fixture
def evaluator():
    return EntryEvaluator()

def test_entry_greater_than(evaluator):
    test_trade = {
        "entry_condition": ">=",
        "entry_rules": [{"primary_source": "Custom", "condition": ">=", "secondary_source": "Custom", "value": 100}]
    }
    assert evaluator.evaluate_entry(test_trade, 105) == True
    assert evaluator.evaluate_entry(test_trade, 99) == False

def test_entry_less_than(evaluator):
    test_trade = {
        "entry_condition": "<=",
        "entry_rules": [{"primary_source": "Custom", "condition": "<=", "secondary_source": "Custom", "value": 100}]
    }
    assert evaluator.evaluate_entry(test_trade, 95) == True
    assert evaluator.evaluate_entry(test_trade, 101) == False

def test_entry_missing_rule_price_fallback(evaluator):
    test_trade = {
        "entry_condition": ">=",
        "entry_rules": [{"primary_source": "Custom", "condition": ">=", "secondary_source": "Custom", "value": 200}]
    }
    # no entry_rule_price set, so should fallback to entry_trigger
    assert evaluator.evaluate_entry(test_trade, 201) == True

def test_entry_unsupported_rule(evaluator):
    test_trade = {
        "entry_condition": ">=",
        "entry_rules": [{"primary_source": "MovingAverage", "condition": ">=", "secondary_source": "Custom", "value": 100}]
    }
    assert evaluator.evaluate_entry(test_trade, 110) == False
