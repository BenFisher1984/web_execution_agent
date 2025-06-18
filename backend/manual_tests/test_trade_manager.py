from backend.engine.ib_client import IBClient
from backend.engine.trade_manager import TradeManager


if __name__ == "__main__":
    client = IBClient()
    client.connect()

    manager = TradeManager(client)
    manager.evaluate_trades()

    client.disconnect()
