Broker-Agnostic Migration — step-by-step playbook
Outcome: a single adapter interface that every backend service talks to, with IBAdapter as the first concrete implementation. All IB-specific code is isolated, so adding AlpacaAdapter, FIXFuturesAdapter, etc. later means writing one new file—not touching the core engine.

1 Define the neutral contract layer
Create backend/core/domain.py

python
Copy
Edit
class NeutralOrder(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    qty: int
    order_type: Literal["MARKET", "LIMIT", "STOP"]
    tif: Literal["DAY", "GTC"]
    price: float | None = None

class FillEvent(BaseModel):
    broker: str
    local_id: str          # our id
    broker_id: str         # returned by broker
    symbol: str
    qty: int
    price: float
    ts: datetime

class Position(BaseModel):
    symbol: str
    qty: int
    avg_price: float
Add Order/Trade status enums here (currently in status_enums.py) so every adapter shares the same vocabulary.

2 Create the adapter interface & factory
bash
Copy
Edit
backend/engine/adapters/
    __init__.py
    base.py          # AdapterBase
    factory.py       # get_adapter("ib")
    ib/
        __init__.py
        adapter.py   # IBAdapter
base.py

python
Copy
Edit
class AdapterBase(ABC):
    name: str
    async def connect(self): ...
    async def disconnect(self): ...
    async def place_order(self, order: NeutralOrder) -> str: ...
    async def cancel_order(self, broker_id: str): ...
    async def stream_fills(self) -> AsyncIterator[FillEvent]: ...
    async def get_positions(self) -> list[Position]: ...
    async def get_market_price(self, symbol: str) -> float: ...
    async def get_history(self, symbol: str, days:int) -> list[Bar]: ...
factory.py

python
Copy
Edit
_adapters = {"ib": IBAdapter}

def get(name="ib") -> AdapterBase:
    return _adapters[name]()
The proposed signature matches the sketch already captured in your TO DO doc TO DO - Broker‑Agnostic….

3 Port ib_client.py → adapter/ib/adapter.py
Move every method in ib_client.py into IBAdapter, keeping the exact behaviour (market data, contract cache, etc.) ib_client.

Replace global ib_client = IBClient() at the bottom with an instance created by the factory.

Bonus: fold ib_connection_manager.py watchdog logic into IBAdapter.connect()/disconnect() ib_connection_manager, so there’s one place that owns reconnection.

4 Refactor execution services to depend on AdapterBase
Service	Change
order_executor.py	Replace from backend.engine.ib_client import IBClient with AdapterBase; remove direct ib_insync imports. Use await adapter.place_order(...) & await adapter.cancel_order(...) instead order_executor.
tick_handler.py	Replace ib.subscribe_* calls with await adapter.subscribe_market_data(...) (add to interface) tick_handler.
trade_manager.py	Inject adapter: AdapterBase; swap all self.ib.* calls for adapter equivalents (price, history, positions) trade_manager.
ticker_routes.py	The helper build_ticker_payload() calls IB methods directly tick_handler. Replace with adapter. Accept a broker query param and pass it to the factory.
app.py	Instantiate once: adapter = get_adapter(settings.default_broker) then pass to TradeManager, TickHandler, etc. app

No change is required for indicator/evaluator modules—they’re broker-agnostic already.

5 Configuration & dependency injection
Extend settings.json to hold { "default_broker": "ib", "ib": { "host": "...", "port": ... } }.

At startup read this file, create the adapter via factory, call await adapter.connect(), and stash it in a FastAPI state object for route handlers.

6 Schema & validation tweaks
Add "broker": { "type": "string", "default": "ib" } to trade_schema.json and treat it as optional for now trade_schema.

Update validation.py to ensure the supplied broker is one your factory knows.

7 Tests
Replace ib_insync.IB().* stubs with a FakeAdapter that implements AdapterBase.

Parametrize integration tests so they can run against a live IB paper account or the fake adapter.

8 Gradual roll-out sequence
Commit 1: add domain models, AdapterBase & factory (compiles but unused).

Commit 2: port ib_client → IBAdapter; update factory.

Commit 3: refactor order_executor only (unit-test place/cancel).

Commit 4: refactor trade_manager, tick_handler, ticker_routes.

Commit 5: wire FastAPI startup to use adapter; delete global ib_client.

Commit 6: add config, broker field to schema, update validation.

Commit 7: remove ib_connection_manager.py or leave it as a thin alias that calls adapter methods (temporary safety-net).

Commit 8: green-path E2E test with IB paper account; merge to main.

Commit 9: introduce AlpacaAdapter skeleton to prove the concept.

9 Files you can delete after migration
ib_client.py (fully subsumed by IBAdapter).

ib_connection_manager.py (logic folded in).

Any IB-specific enums duplicated elsewhere.