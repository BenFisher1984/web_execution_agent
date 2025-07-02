import pytest
from backend.engine.take_profit_evaluator import TakeProfitEvaluator

@pytest.fixture
def evaluator():
    return TakeProfitEvaluator()

def test_take_profit_long_triggered(evaluator):
    trade = {
        "take_profit_type": "Custom",
        "take_profit_price": 110,
        "direction": "Long"
    }
    result = evaluator.evaluate_take_profit(trade, 115)
    assert result["triggered"] == True
    result = evaluator.evaluate_take_profit(trade, 105)
    assert result["triggered"] == False

def test_take_profit_short_triggered(evaluator):
    trade = {
        "take_profit_type": "Custom",
        "take_profit_price": 90,
        "direction": "Short"
    }
    result = evaluator.evaluate_take_profit(trade, 85)
    assert result["triggered"] == True
    result = evaluator.evaluate_take_profit(trade, 95)
    assert result["triggered"] == False

def test_take_profit_missing_fields(evaluator):
    trade = {
        "take_profit_type": None,
        "take_profit_price": None,
        "direction": "Long"
    }
    result = evaluator.evaluate_take_profit(trade, 100)
    assert result["triggered"] == False
