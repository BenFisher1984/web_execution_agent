📄 Trading Engine Test Roadmap
Below is a structured test plan covering unit tests, integration tests, and stress/performance tests — exactly how professional trading teams would approach it.

✅ 1️⃣ Unit Tests (pure logic)
EntryEvaluator:

test Long: >= crossing

test Short: <= crossing

test fallback to entry_trigger

test unsupported rule

test entry direction safety if entry_condition is invalid

test edge cases (e.g. entry_rule_price = 0)

StopLossEvaluator:

test standard stop-loss triggering

test trailing stop triggering

test active stop with both configured (long/short)

test missing initial stop (should log warning)

test missing trailing stop

test direction logic with short

test negative stop prices (invalid)

TakeProfitEvaluator:

test take-profit triggered for Long

test take-profit triggered for Short

test missing TP price

test extreme TP price (huge)

test direction logic edge

✅ 2️⃣ TradeManager methods (integration logic)
evaluate_trades:

trade moves from Active → Entry Order Submitted

trade remains Active if price not crossed

trade status with missing fields (no direction, no symbol)

trade missing quantity

trade with invalid enum status

evaluate_trade_on_tick:

triggers entry on tick

triggers take-profit on tick

triggers stop-loss on tick

updates risk parameters on tick

handles missing active stop gracefully

handles missing volatility data

handles corrupted volatility cache

mark_trade_filled:

moves to Live correctly

sets stop properly

sets take-profit properly

sets dollar/percent at risk correctly

handles no active stop (should log and continue)

handles short direction

handles missing trailing stop

handles bad fill quantity

mark_trade_closed:

moves to Inactive

closes trade with correct timestamps

handles partial exit qty

handles zero exit qty

handles missing trade

load_portfolio_value:

correct parsing of portfolio config

missing file

invalid JSON

zero portfolio value

negative portfolio value

save/load trades:

correct save/load of multiple trades

corrupted trade file

missing trade file

no disk permissions

✅ 3️⃣ Broker / IB client behavior (mocked):
fill confirmation events

order submission failure

partial fill

network reconnect

IB returns zero position

IB returns inconsistent average cost

IB throws exception (API error)

✅ 4️⃣ High-level business rules:
cannot activate a trade with no initial stop

cannot activate if quantity is zero

cannot mark filled if status is not Entry Order Submitted

cannot mark closed if not Contingent Order Submitted

no duplicate symbols in the trade list

always store trades in saved_trades.json on status change

✅ 5️⃣ Stress / Performance:
simulate 1000 trades, tick triggers on each

simulate 1000 trades with active PnL calculations

10,000 ticks per second for one trade

latency measurement

disk IO stress (trades saving repeatedly)

random disk write failures

✅ 6️⃣ Validation rules (future advanced validation.py):
mandatory fields presence

enum consistency

direction vs entry condition mismatch

negative prices

risk over 100%

entry/exit symbols match portfolio symbols

duplicate order IDs

no missing time_in_force or order_type

🚀 Summary + Next Steps
✅ This roadmap sets you up for a production-grade test suite that grows with your program.

You do not need to do them all at once, but you can gradually pick them off, systematically hardening each area.