import pytest
from backend.engine.stop_loss_evaluator import StopLossEvaluator

@pytest.fixture
def evaluator():
    return StopLossEvaluator()

def test_short_stop_loss_triggered(evaluator):
    trade = {
        "stop_loss": 105,
        "trailing_stop": None,
        "direction": "Short"
    }
    # price goes ABOVE stop price, short trade stops out
    result = evaluator.evaluate_stop(trade, 110)
    assert result["triggered"] == True
    # price below stop price, should not trigger
    result = evaluator.evaluate_stop(trade, 100)
    assert result["triggered"] == False

def test_short_trailing_stop_triggered(evaluator):
    trade = {
        "stop_loss": None,
        "trailing_stop": 103,
        "direction": "Short"
    }
    result = evaluator.evaluate_stop(trade, 104)
    assert result["triggered"] == True
    result = evaluator.evaluate_stop(trade, 101)
    assert result["triggered"] == False

def test_short_both_stops_selects_lower(evaluator):
    trade = {
        "stop_loss": 105,
        "trailing_stop": 102,
        "direction": "Short"
    }
    result = evaluator.evaluate_stop(trade, 103)
    # active stop should be the min (102)
    assert result["stop_price"] == 102
    # price above 102 triggers
    assert result["triggered"] == True

def test_short_no_stops(evaluator):
    trade = {
        "stop_loss": None,
        "trailing_stop": None,
        "direction": "Short"
    }
    result = evaluator.evaluate_stop(trade, 100)
    assert result["triggered"] == False
