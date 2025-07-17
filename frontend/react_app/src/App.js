import React, { useEffect, useState } from 'react';
import { useStatusPoll } from "./hooks/useStatusPoll";
import { useTickerLookup } from "./hooks/useTickerLookup";
import TradeTable from "./components/TradeTable";
import LayoutEditor from "./components/LayoutEditor";
import DeleteModal from "./components/DeleteModal";
import PortfolioPanel from "./components/PortfolioPanel";
import EntryRulesPanel from "./components/EntryRulesPanel";
import StopRulesPanel from "./components/StopRulesPanel";
import TrailingStopRulesPanel from "./components/TrailingStopRulesPanel";
import TakeProfitRulesPanel from "./components/TakeProfitRulesPanel";
import QuickEntryPanel from "./components/QuickEntryPanel";
import TradeSizePanel from "./components/TradeSizePanel";
import { createHandleInputChange } from "./utils/handleInputChange";

const flattenToFlat = (obj, prefix = "", res = {}) => {
  for (const key in obj) {
    const val = obj[key];
    const newKey = prefix ? `${prefix}.${key}` : key;
    if (typeof val === "object" && val !== null && !Array.isArray(val)) {
      flattenToFlat(val, newKey, res);
    } else if (Array.isArray(val)) {
      // Handle arrays by flattening each element with its index
      val.forEach((item, index) => {
        if (typeof item === "object" && item !== null) {
          flattenToFlat(item, `${newKey}.${index}`, res);
        } else {
          res[`${newKey}.${index}`] = item;
        }
      });
    } else {
      res[newKey] = val;
    }
  }
  return res;
};

const safeToFixed = (val, digits = 2) =>
  isFinite(Number(val)) && Number(val) !== 0
    ? Number(val).toFixed(digits)
    : "--";

const safeDollar = (val) =>
  isFinite(Number(val)) && Number(val) !== 0
    ? `$${Number(val).toFixed(0)}`
    : "--";

const formatOrderStatus = (status) => {
  const normalized = (status || "").toLowerCase();

  const pillStyles = {
    "inactive": "bg-gray-400 text-white",
    "active": "bg-blue-500 text-white",
    "entry order submitted": "bg-yellow-500 text-black",
    "contingent order active": "bg-indigo-600 text-white",
    "contingent order submitted": "bg-purple-600 text-white",
  };

  const labelMap = {
    "inactive": "Inactive",
    "active": "Active",
    "entry order submitted": "Entry Submitted",
    "contingent order active": "Contingent Active",
    "contingent order submitted": "Contingent Submitted",
  };

  return (
    <span className={`font-bold px-2 py-1 rounded text-sm ${pillStyles[normalized] || "bg-gray-200 text-black"}`}>
      {labelMap[normalized] || status}
    </span>
  );
};

function App() {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const apiStatus = useStatusPoll();
  const [currentTime, setCurrentTime] = useState("");
  const [timezoneDisplay, setTimezoneDisplay] = useState("Australia/Sydney");
  const [resetTime, setResetTime] = useState("");
  const [resetTimezone, setResetTimezone] = useState("");
  const [layoutConfig, setLayoutConfig] = useState([]);
  const [modifyLayoutMode, setModifyLayoutMode] = useState(false);
  const [layoutDraft, setLayoutDraft] = useState([]);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [tradeToDelete, setTradeToDelete] = useState(null);
  const { lookupTicker } = useTickerLookup();
  const [selectedTradeIndex, setSelectedTradeIndex] = useState(0);

  // Function to fetch indicator values from backend
  const fetchIndicatorValue = async (symbol, indicator, lookback = 8) => {
    try {
      const response = await fetch(`http://localhost:8000/indicator-value?symbol=${symbol}&indicator=${indicator}&lookback=${lookback}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch indicator value: ${response.statusText}`);
      }
      const data = await response.json();
      return data.value;
    } catch (error) {
      console.error(`Error fetching ${indicator} value for ${symbol}:`, error);
      return null;
    }
  };

  // Enhanced handleInputChange that fetches indicator values
  const handleInputChangeWithIndicatorFetch = async (index, field, value, trades) => {
    const trade = trades[index];
    
    // Check if this is a secondary_source change that should trigger indicator calculation
    if (field.includes('secondary_source') && value !== 'Custom') {
      const symbol = trade.symbol;
      if (symbol) {
        // Map dropdown values to indicator names
        const indicatorMap = {
          'EMA 8': 'ema',
          'SMA 8': 'sma', 
          'EMA 21': 'ema',
          'SMA 21': 'sma',
          'ADR': 'adr',
          'ATR': 'atr'
        };
        
        const indicator = indicatorMap[value];
        const lookback = value.includes('8') ? 8 : value.includes('21') ? 21 : 14;
        
        if (indicator) {
          console.log(`Fetching ${indicator} value for ${symbol}...`);
          const indicatorValue = await fetchIndicatorValue(symbol, indicator, lookback);
          
          if (indicatorValue !== null) {
            // Update the corresponding value field
            const valueField = field.replace('secondary_source', 'value');
            console.log(`Setting ${valueField} to ${indicatorValue}`);
            
            // Call the original handleInputChange to update the value
            handleInputChange(index, valueField, indicatorValue, trades);
          }
        }
      }
    }
    
    // Call the original handleInputChange
    handleInputChange(index, field, value, trades);
  };

  const [portfolio, setPortfolio] = useState({
    "portfolio_value": 0,
    use_pnl_offset: "No",
    max_risk: 0,
  });

  const updatePortfolio = (key, value) => {
    const updated = { ...portfolio, [key]: value };
    setPortfolio(updated);
    fetch("http://localhost:8000/portfolio_config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updated),
    });
  };

  const numericFields = new Set([
    "entry_trigger",
    "initial_stop_price",
    "risk_pct",
    "percent_at_risk",
    "dollar_at_risk",
    "pnl_percent",
    "pnl_dollar"
  ]);

  const calculateQuantity = (trade, portfolioValue) => {
    // Use correct field names and structure
    const riskPct = Number(trade.percent_risk);
    const entry = Number(trade.entry_rules?.[0]?.value);
    const stop = Number(trade.initial_stop_rules?.[0]?.value);
    const direction = (trade.direction || "").toLowerCase();
    const capital = Number(portfolioValue);

    if (!["long", "short"].includes(direction)) {
      return null;
    }

    if (
      isNaN(riskPct) || riskPct <= 0 ||
      isNaN(entry) || entry <= 0 ||
      isNaN(stop) || stop <= 0 ||
      isNaN(capital) || capital <= 0
    ) {
      return null;
    }

    if (direction === "long" && stop >= entry) {
      return null;
    }

    if (direction === "short" && stop <= entry) {
      return null;
    }

    const riskAmount = (capital * riskPct) / 100;
    const riskPerShare = Math.abs(entry - stop);
    const qty = Math.floor(riskAmount / riskPerShare);
    return qty > 0 ? qty : null;
  };

  const liveRisk = trades.reduce((sum, t) => sum + (parseFloat(t.percent_at_risk) || 0), 0);
  const livePnl = trades.reduce((sum, t) => sum + (parseFloat(t.pnl_percent) || 0), 0);
  const netRisk = portfolio.use_pnl_offset === "Yes" ? liveRisk + livePnl : liveRisk;
  const layout = layoutConfig.map((section) => ({
    section: section.section,
    fields: (section.fields || []).filter((f) => f.enabled !== false),
  }));

  const flattenToNested = (flat) => {
    const nested = {};
    Object.entries(flat).forEach(([key, val]) => {
      if (key.includes(".")) {
        const parts = key.split(".");
        let current = nested;
        
        for (let i = 0; i < parts.length - 1; i++) {
          const part = parts[i];
          const nextPart = parts[i + 1];
          
          // If next part is numeric, current part should be an array
          if (!isNaN(nextPart)) {
            if (!Array.isArray(current[part])) {
              current[part] = [];
            }
            if (!current[part][parseInt(nextPart)]) {
              current[part][parseInt(nextPart)] = {};
            }
            current = current[part][parseInt(nextPart)];
            i++; // Skip the numeric index
          } else {
            if (!current[part]) {
              current[part] = {};
            }
            current = current[part];
          }
        }
        
        // Set the final value
        const finalKey = parts[parts.length - 1];
        current[finalKey] = val;
      } else {
        nested[key] = val;
      }
    });
    return nested;
  };

  const buyingPower = portfolio.max_risk - netRisk;

  const isTradeValid = (trade) => {
    for (const section of layout) {
      for (const field of section.fields || []) {
        if (field.mandatory) {
          const value = trade[field.key];
          if (value === undefined || value === null || value === "") {
            return false;
          }
        }
      }
    }
    return true;
  };
  
  // 🆕 Flatten layoutConfig fields
  const getAllFields = () => {
    return layoutConfig.flatMap((section) => section.fields || []);
  };

  // Add this helper function at the top-level (inside App.js, outside of App function)
  const allowedTradeFields = [
    "symbol",
    "calculated_quantity",
    "usd",
    "percent_balance",
    "usd_risk",
    "percent_risk",
    "direction",
    "time_in_force",
    "order_type",
    "entry_rules",
    "initial_stop_rules",
    "trailing_stop_rules",
    "take_profit_rules"
    // add any other schema fields here if needed
  ];

  function filterTradeForBackend(trade) {
    const filtered = {};
    for (const key of allowedTradeFields) {
      if (trade[key] !== undefined) filtered[key] = trade[key];
    }
    return filtered;
  }

  useEffect(() => {
    // Load portfolio config
    fetch("http://localhost:8000/portfolio_config")
      .then((res) => res.json())
      .then((data) => setPortfolio(data)); 
    // Load trades
    fetch("http://localhost:8000/trades")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch trades");
        return res.json();
      })
      .then((data) => {
        const cleaned = data.map((trade) => {
          const flat = flattenToFlat(trade);
          const cleanedFlat = {};
          for (const [key, val] of Object.entries(flat)) {
            const isNumeric = numericFields.has(key);
            const num = isNumeric ? Number(val) : val;
            cleanedFlat[key] = num;
          }
          return flattenToNested(cleanedFlat);
        });
        setTrades(cleaned);
        setLoading(false);
      })


      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });

    // Load schedule
    fetch("http://localhost:8000/get_schedule")
      .then((res) => res.json())
      .then((data) => {
        setResetTime(data.reset_time || "");
        setResetTimezone(data.timezone || "Australia/Sydney");
      });

    // Load layout
    fetch("http://localhost:8000/layout_config")
      .then(res => res.json())
      .then(data => {
        setLayoutConfig(data);
      });

    // Load trade count
    fetch("http://localhost:8000/trade_config")
      .then(res => res.json())
      .then(data => {
        // Do not overwrite trades — only log
      });
  
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: timezoneDisplay,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });
      setCurrentTime(formatter.format(new Date()));
    }, 1000);
    return () => clearInterval(interval);
  }, [timezoneDisplay]);

  const handleActivate = async (index) => {
    const trade = flattenToFlat(trades[index]);
    const nestedTrade = flattenToNested(trade);
    const portfolioForBackend = portfolio;

    // Add debug log for outgoing trade object
    console.log('🚀 Outgoing trade object for validation:', JSON.stringify(nestedTrade, null, 2));
    console.log('🔎 USD field type:', typeof nestedTrade.usd, 'value:', nestedTrade.usd);

    // Calculate quantity and validate
    const calcQty = calculateQuantity(nestedTrade, portfolio.portfolio_value);
    if (!calcQty || isNaN(calcQty) || calcQty <= 0) {
      alert("❌ Cannot activate trade: Invalid quantity. Check percent_risk, entry_rule, initial_stop_rule, and direction.");
      return;
    }

    // Ensure calculated_quantity is up to date
    nestedTrade.calculated_quantity = calcQty;

    // Filter trade for backend (if needed)
    const filteredTrade = filterTradeForBackend(nestedTrade);

    try {
      const validationRes = await fetch("http://localhost:8000/validate_trade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ trade: filteredTrade, portfolio: portfolioForBackend })
      });

      const validationResult = await validationRes.json();
      if (!validationResult.valid) {
        alert("❌ Validation failed: " + validationResult.reason);
        return;
      }

      const activationRes = await fetch("http://localhost:8000/activate_trade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ trade: filteredTrade, portfolio: portfolioForBackend })
      });

      if (!activationRes.ok) {
        const errorText = await activationRes.text();
        throw new Error(`Activation failed: ${errorText}`);
      }

      const text = await activationRes.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch (e) {
        throw new Error(`Invalid JSON in activation response: ${text}`);
      }

      const updated = [...trades];
      updated[index].order_status = "active";
      updated[index].trade_status = data.trade?.trade_status ?? "Pending";
      updated[index].calculated_quantity = data.trade?.calculated_quantity ?? null;
      updated[index].action = "--";
      setTrades(updated);

      await fetch("http://localhost:8000/save_trades", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updated)
      });

    } catch (err) {
      alert("❌ Activation failed: " + err.message);
      const updated = [...trades];
      updated[index].order_status = "pending";
      setTrades(updated);
    }
  };

  const handleInputChange = createHandleInputChange({
    getAllFields,
    calculateQuantity,
    setTrades,
    portfolio,
    flattenToFlat,
    flattenToNested,
    handleActivate,
  });








  const handleScheduleUpdate = () => {
    fetch("http://localhost:8000/set_schedule", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ reset_time: resetTime, timezone: resetTimezone })
    })
      .then((res) => res.json())
      .then((data) => alert(data.message))
      .catch(() => alert("Failed to update reset schedule."));
  };

  if (loading) return <div className="p-4">Loading trades...</div>;
  if (error) return <div className="p-4 text-red-600">Error: {error}</div>;

  return (
    <div className="p-4">
      {/* Header Row */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-8">
          <h1 className="text-xl font-semibold">Execution Agent</h1>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">API STATUS:</span>
            <span className={`px-3 py-1 rounded font-bold text-white ${apiStatus === "CONNECTED" ? "bg-green-600" : "bg-red-600"}`}>{apiStatus}</span>
          </div>
          {/* Timezone/Reset Controls */}
          <div className="flex items-center gap-4 text-sm ml-8">
            <div className="flex items-center gap-1">
              <span className="text-gray-500">Timezone:</span>
              <span className="ml-1 text-gray-800">{timezoneDisplay}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-gray-500">Current Time:</span>
              <span className="ml-1 text-gray-800">{currentTime}</span>
            </div>
            <div className="flex items-center gap-1">
              <label className="text-gray-500">Reset Time:</label>
              <input
                type="text"
                value={resetTime}
                onChange={(e) => setResetTime(e.target.value)}
                className="border rounded px-2 py-1 w-16 text-right"
                style={{ minWidth: 0 }}
              />
            </div>
            <div className="flex items-center gap-1">
              <label className="text-gray-500">Reset TZ:</label>
              <input
                type="text"
                value={resetTimezone}
                onChange={(e) => setResetTimezone(e.target.value)}
                className="border rounded px-2 py-1 w-28 text-right"
                style={{ minWidth: 0 }}
              />
            </div>
            <button
              onClick={handleScheduleUpdate}
              className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600 ml-2"
              style={{ whiteSpace: 'nowrap' }}
            >
              Set Reset Time
            </button>
          </div>
        </div>
      </div>
      {/* Rule Panels Row */}
      <div className="flex flex-row gap-4 mb-6">
        <PortfolioPanel
          portfolio={portfolio}
          updatePortfolio={updatePortfolio}
          liveRisk={liveRisk}
          livePnl={livePnl}
          buyingPower={buyingPower}
          safeToFixed={safeToFixed}
        />
        <TradeSizePanel 
          tradeSize={trades[selectedTradeIndex] || {}} 
          onChange={(field, value) => handleInputChangeWithIndicatorFetch(selectedTradeIndex, field, value, trades)}
        />
        <EntryRulesPanel 
          entryRules={trades[selectedTradeIndex]?.entry_rules || []} 
          onChange={(field, value) => handleInputChangeWithIndicatorFetch(selectedTradeIndex, field, value, trades)}
        />
        <StopRulesPanel 
          initialStopRules={trades[selectedTradeIndex]?.initial_stop_rules || []} 
          onChange={(field, value) => handleInputChangeWithIndicatorFetch(selectedTradeIndex, field, value, trades)}
        />
        <TrailingStopRulesPanel 
          trailingStopRules={trades[selectedTradeIndex]?.trailing_stop_rules || []} 
          onChange={(field, value) => handleInputChangeWithIndicatorFetch(selectedTradeIndex, field, value, trades)}
        />
        <TakeProfitRulesPanel 
          takeProfitRules={trades[selectedTradeIndex]?.take_profit_rules || []} 
          onChange={(field, value) => handleInputChangeWithIndicatorFetch(selectedTradeIndex, field, value, trades)}
        />
        <QuickEntryPanel trade={trades[selectedTradeIndex] || {}} />
      </div>

      <div className="mb-2 flex gap-2">
        <button
          onClick={() => {
            setLayoutDraft(JSON.parse(JSON.stringify(layoutConfig)));
            setModifyLayoutMode(true);
          }}
          className="bg-blue-600 text-white text-sm px-4 py-1 rounded hover:bg-blue-700"
        >
          Modify Layout
        </button>

        <button
          onClick={() => {
            setTrades(prev => [...prev, { editing: true }]);
          }}
          className="bg-green-600 text-white text-sm px-4 py-1 rounded hover:bg-green-700"
        >
          Add Trade
        </button>

        <button
          onClick={() => setShowDeleteModal(true)}
          className="bg-red-600 text-white text-sm px-4 py-1 rounded hover:bg-red-700"
        >
          Delete Trade
        </button>

        <button
          onClick={() => {
            fetch("http://localhost:8000/save_trades", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(trades)
            })
              .then(res => {
                if (!res.ok) throw new Error("Failed to save trades");
                return res.json();
              })
              .then((data) => {
                console.log("📦 Saved trades:", data.message);
                alert(`Trades saved! ${data.message}`);
              })
              .catch(err => {
                console.error("❌ Error saving trades:", err);
                alert("Failed to save trades.");
              });
          }}
          className="bg-yellow-500 text-white text-sm px-4 py-1 rounded hover:bg-yellow-600"
        >
          Save Trades
        </button>
      </div>

  <TradeTable
  trades={trades}
  layout={layout}
  handleInputChange={handleInputChangeWithIndicatorFetch}
  getAllFields={getAllFields}
  numericFields={numericFields}
  lookupTicker={lookupTicker}
  setTrades={setTrades} // Pass setTrades as a prop
  selectedTradeIndex={selectedTradeIndex}
  onSelectTrade={setSelectedTradeIndex}
/>
  

{modifyLayoutMode && (
  <LayoutEditor
    layoutDraft={layoutDraft}
    setLayoutDraft={setLayoutDraft}
    onSave={() => {
      fetch("http://localhost:8000/layout_config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(layoutDraft),
      })
        .then((res) => {
          if (!res.ok) throw new Error("Failed to save layout");
          return res.json();
        })
        .then(() => {
          setLayoutConfig(layoutDraft);
          setModifyLayoutMode(false);
        })
        .catch((err) => {
          console.error("❌ Error saving layout:", err);
          alert("Failed to save layout.");
        });
    }}
    onCancel={() => setModifyLayoutMode(false)}
  />
)}

{showDeleteModal && (
  <DeleteModal
    trades={trades}
    tradeToDelete={tradeToDelete}
    setTradeToDelete={setTradeToDelete}
    setShowDeleteModal={setShowDeleteModal}
    setTrades={setTrades}
  />
)}


    <div className="mt-6 text-center text-base italic text-gray-600 border-t pt-4">
      “Whenever I enter a position, I have a predetermined stop. That is the only way I can sleep.
      I know where I'm getting out before I get in. The position size on a trade is determined by the stop,
      and the stop is determined on a technical basis.” — <span className="font-medium">Bruce Kovner</span>
  </div>
</div>  
);
}

export default App;
