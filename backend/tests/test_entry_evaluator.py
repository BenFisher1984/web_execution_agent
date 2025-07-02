import pytest
from backend.engine.entry_evaluator import EntryEvaluator

@pytest.fixture
def evaluator():
    return EntryEvaluator()

def test_entry_greater_than(evaluator):
    trade = {
        "entry_condition": ">=",
        "entry_rule": "Custom",
        "entry_rule_price": 100
    }
    assert evaluator.evaluate_entry(trade, 105) == True
    assert evaluator.evaluate_entry(trade, 99) == False

def test_entry_less_than(evaluator):
    trade = {
        "entry_condition": "<=",
        "entry_rule": "Custom",
        "entry_rule_price": 100
    }
    assert evaluator.evaluate_entry(trade, 95) == True
    assert evaluator.evaluate_entry(trade, 101) == False

def test_entry_missing_rule_price_fallback(evaluator):
    trade = {
        "entry_condition": ">=",
        "entry_rule": "Custom",
        "entry_trigger": 200
    }
    # no entry_rule_price set, so should fallback to entry_trigger
    assert evaluator.evaluate_entry(trade, 201) == True

def test_entry_unsupported_rule(evaluator):
    trade = {
        "entry_condition": ">=",
        "entry_rule": "MovingAverage",  # unsupported currently
        "entry_rule_price": 100
    }
    assert evaluator.evaluate_entry(trade, 110) == False
