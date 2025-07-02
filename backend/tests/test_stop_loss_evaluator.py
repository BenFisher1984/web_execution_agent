import pytest
from backend.engine.stop_loss_evaluator import StopLossEvaluator

@pytest.fixture
def evaluator():
    return StopLossEvaluator()

def test_stop_loss_only_triggered(evaluator):
    trade = {
        "stop_loss": 95,
        "trailing_stop": None
    }
    # price below stop-loss should trigger
    result = evaluator.evaluate_stop(trade, 90)
    assert result["triggered"] == True
    # price above stop-loss should not trigger
    result = evaluator.evaluate_stop(trade, 100)
    assert result["triggered"] == False

def test_trailing_stop_only_triggered(evaluator):
    trade = {
        "stop_loss": None,
        "trailing_stop": 97
    }
    result = evaluator.evaluate_stop(trade, 95)
    assert result["triggered"] == True
    result = evaluator.evaluate_stop(trade, 99)
    assert result["triggered"] == False

def test_both_stops_chooses_higher(evaluator):
    trade = {
        "stop_loss": 95,
        "trailing_stop": 98
    }
    result = evaluator.evaluate_stop(trade, 97)
    # active stop should be trailing at 98
    assert result["stop_price"] == 98
    # price below 98 triggers
    assert result["triggered"] == True

def test_no_stops(evaluator):
    trade = {
        "stop_loss": None,
        "trailing_stop": None
    }
    result = evaluator.evaluate_stop(trade, 90)
    assert result["triggered"] == False
