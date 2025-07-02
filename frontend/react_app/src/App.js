import React, { useEffect, useState } from 'react';
import { useStatusPoll } from "./hooks/useStatusPoll";
import { useTickerLookup } from "./hooks/useTickerLookup";
import TradeTable from "./components/TradeTable";
import LayoutEditor from "./components/LayoutEditor";
import DeleteModal from "./components/DeleteModal";
import PortfolioPanel from "./components/PortfolioPanel";
import { createHandleInputChange } from "./utils/handleInputChange";






  const flattenToFlat = (obj, prefix = "", res = {}) => {
    for (const key in obj) {
      const val = obj[key];
      const newKey = prefix ? `${prefix}.${key}` : key;
      if (typeof val === "object" && val !== null && !Array.isArray(val)) {
        flattenToFlat(val, newKey, res);
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
    const riskPct = Number(trade.risk_pct);
    const entry = Number(trade.entry_rule_price);
    const stop = Number(trade.initial_stop_price);
    const direction = (trade.direction || "").toLowerCase();
    const capital = Number(portfolioValue);

    if (!["long", "short"].includes(direction)) {
      console.log("❌ Missing or invalid direction:", direction);
      return null;
    }

    if (
      isNaN(riskPct) || riskPct <= 0 ||
      isNaN(entry) || entry <= 0 ||
      isNaN(stop) || stop <= 0 ||
      isNaN(capital) || capital <= 0
    ) {
      console.log("❌ Missing required numeric input", { riskPct, entry, stop, capital });
      return null;
    }

    if (direction === "long" && stop >= entry) {
      console.log("❌ Invalid stop for Long: stop >= entry", { stop, entry });
      return null;
    }

    if (direction === "short" && stop <= entry) {
      console.log("❌ Invalid stop for Short: stop <= entry", { stop, entry });
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
    fields: section.fields.filter((f) => f.enabled !== false),
  }));

  const flattenToNested = (flat) => {
    const nested = {};
    Object.entries(flat).forEach(([key, val]) => {
      if (key.includes(".")) {
        const [parent, child] = key.split(".");
        nested[parent] = nested[parent] || {};
        nested[parent][child] = val;
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
  return layoutConfig.flatMap((section) => section.fields);
};

  useEffect(() => {
    // Load portfolio config
    fetch("http://localhost:8000/portfolio_config")
      .then((res) => res.json())
      .then((data) => setPortfolio(data)); 
    console.log("🛠 useEffect running on mount");
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
            console.log(`🧼 ${key}:`, val, "→", num, `(${typeof num})`);
            cleanedFlat[key] = num;
          }
          return flattenToNested(cleanedFlat);
        });
        console.log("✅ Cleaned Trades Ready:", cleaned);
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
        console.log("🎨 Loaded layout:", data);
        setLayoutConfig(data);
      });

    // Load trade count
    fetch("http://localhost:8000/trade_config")
      .then(res => res.json())
      .then(data => {
        console.log("🧾 Loaded trade count:", data.num_trades);
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

  // Calculate quantity and validate
  const calcQty = calculateQuantity(nestedTrade, portfolio.portfolio_value);
  if (!calcQty || isNaN(calcQty) || calcQty <= 0) {
    alert("❌ Cannot activate trade: Invalid quantity. Check risk_pct, entry_trigger, initial_stop_price, and direction.");
    return;
  }

  // Ensure calculated_quantity is a number
  nestedTrade.calculated_quantity = calcQty;

  try {
    const validationRes = await fetch("http://localhost:8000/validate_trade", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trade: nestedTrade, portfolio: portfolioForBackend })
    });

    const validationResult = await validationRes.json();
    if (!validationResult.valid) {
      alert("❌ Validation failed: " + validationResult.reason);
      return;
    }

    const activationRes = await fetch("http://localhost:8000/activate_trade", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trade: nestedTrade, portfolio: portfolioForBackend })
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
    updated[index].quantity = data.trade?.quantity ?? null;
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
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center gap-24">
          <h1 className="text-xl font-semibold">Execution Agent</h1>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">API STATUS:</span>
            <span className={`px-3 py-1 rounded font-bold text-white ${apiStatus === "CONNECTED" ? "bg-green-600" : "bg-red-600"}`}>
              {apiStatus}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-2 text-left items-start text-sm">
          <div>
            <span className="text-gray-500">Timezone:</span>
            <span className="ml-2 text-gray-800">{timezoneDisplay}</span>
          </div>
          <div>
            <span className="text-gray-500">Current Time:</span>
            <span className="ml-2 text-gray-800">{currentTime}</span>
          </div>
          <div>
            <label className="block text-gray-500">Reset Time:</label>
            <input
              type="text"
              value={resetTime}
              onChange={(e) => setResetTime(e.target.value)}
              className="border rounded px-2 py-1 w-full"
            />
          </div>
          <div>
            <label className="block text-gray-500">Reset Timezone:</label>
            <input
              type="text"
              value={resetTimezone}
              onChange={(e) => setResetTimezone(e.target.value)}
              className="border rounded px-2 py-1 w-full"
            />
          </div>
          <button
            onClick={handleScheduleUpdate}
            className="mt-1 bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
          >
            Set Reset Time
          </button>
        </div>

      </div>  

      {/* 🆕 Portfolio Section */}
        <PortfolioPanel
  portfolio={portfolio}
  updatePortfolio={updatePortfolio}
  liveRisk={liveRisk}
  livePnl={livePnl}
  buyingPower={buyingPower}
  safeToFixed={safeToFixed}
/>
  



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
            fetch("http://localhost:8000/trade_config", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ num_trades: trades.length })
            })
              .then(res => {
                if (!res.ok) throw new Error("Failed to save trades");
                return res.json();
              })
              .then(() => {
                console.log("📦 Saved trade count:", trades.length);
                alert("Trades saved!");
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
  handleInputChange={handleInputChange}
  getAllFields={getAllFields}
  numericFields={numericFields}
  lookupTicker={lookupTicker}
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
