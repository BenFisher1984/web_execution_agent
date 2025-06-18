import React, { useEffect, useState } from 'react';

function App() {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState("checking...");
  const [currentTime, setCurrentTime] = useState("");
  const [timezoneDisplay, setTimezoneDisplay] = useState("Australia/Sydney");
  const [resetTime, setResetTime] = useState("");
  const [resetTimezone, setResetTimezone] = useState("");

  useEffect(() => {
    // Load trades
    fetch("http://localhost:8000/trades")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch trades");
        return res.json();
      })
      .then((data) => {
        setTrades(data);
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

    // Poll API status
    const interval = setInterval(() => {
      fetch("http://localhost:8000/status")
        .then((res) => res.json())
        .then((data) => setApiStatus(data.status.toUpperCase()))
        .catch(() => setApiStatus("DISCONNECTED"));
    }, 5000);

    return () => clearInterval(interval);
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

  const handleInputChange = (index, field, value) => {
    const updated = [...trades];
    if (field.includes(".")) {
      const [parent, child] = field.split(".");
      if (!updated[index][parent]) updated[index][parent] = {};
      updated[index][parent][child] = value;
    } else {
      updated[index][field] = value;
    }

    if (updated[index].order_status === "active") {
      updated[index].order_status = "pending";
    }

    setTrades(updated);

    fetch("http://localhost:8000/save_trades", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(updated)
    });
  };

  const handleActivate = (index) => {
    const trade = trades[index];

    if (trade.order_status === "active") {
      const updated = [...trades];
      updated[index].order_status = "pending";
      setTrades(updated);
      return;
    }

    fetch("http://localhost:8000/activate_trade", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(trade)
    })
      .then((res) => {
        if (!res.ok) throw new Error("Activation failed");
        return res.json();
      })
      .then((data) => {
        const updated = [...trades];
        updated[index].order_status = "active";
        updated[index].quantity = data.quantity;
        setTrades(updated);

        fetch("http://localhost:8000/save_trades", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(updated)
        });
      })
      .catch((err) => {
        alert("❌ Activation failed: " + err.message);
        const updated = [...trades];
        updated[index].order_status = "pending";
        setTrades(updated);
      });
  };

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
      <div className="mb-4 flex justify-between items-start">
        <div className="flex items-center gap-24">
          <h1 className="text-xl font-semibold">Execution Agent</h1>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">API STATUS:</span>
            <span className={`px-3 py-1 rounded font-bold text-white ${apiStatus === "CONNECTED" ? "bg-green-600" : "bg-red-600"}`}>
              {apiStatus}
            </span>
          </div>
        </div>


        <div className="grid grid-cols-1 gap-2 text-left items-start">

          <div className="flex items-center justify-between gap-2">
            <label className="min-w-[100px]">Timezone:</label>
            <select
              value={timezoneDisplay}
              onChange={(e) => setTimezoneDisplay(e.target.value)}
              className="border px-2 py-1"
            >
              <option value="Australia/Sydney">Australia/Sydney</option>
              <option value="America/New_York">America/New_York</option>
              <option value="UTC">UTC</option>
            </select>
          </div>


          <div className="flex items-center justify-between gap-2">
            <label className="min-w-[100px]">Current Time:</label>
            <div className="border px-3 py-1 font-mono text-sm bg-white rounded">
              {currentTime}
            </div>
          </div>


          <div className="flex items-center justify-between gap-2">
            <label htmlFor="reset-time" className="min-w-[100px]">Reset Time:</label>
            <input
              type="time"
              id="reset-time"
              value={resetTime}
              onChange={(e) => setResetTime(e.target.value)}
              className="border px-2 py-1"
            />
          </div>


          <div className="flex items-center justify-between gap-2">
            <div className="min-w-[100px]"></div>
            <button
              onClick={handleScheduleUpdate}
              className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
            >
              Update Reset Schedule
            </button>
          </div>
        </div>
      </div>

      {/* Existing Trade Table Follows */}

      <table className="table-auto border-collapse w-full text-sm">
        <thead>
          <tr className="bg-gray-200 whitespace-nowrap">
            <th className="border px-2 py-1 text-center whitespace-nowrap">Activate Order?</th>
            <th className="border px-2 py-1">Symbol</th>
            <th className="border px-2 py-1">Trade Status</th>
            <th className="border px-2 py-1">Direction</th>
            <th className="border px-2 py-1">Entry Trigger</th>
            <th className="border px-2 py-1">Stop Type</th>
            <th className="border px-2 py-1">Stop Price</th>
            <th className="border px-2 py-1">Trailing Type</th>
            <th className="border px-2 py-1">Trailing Price</th>
            <th className="border px-2 py-1">Portfolio</th>
            <th className="border px-2 py-1">Risk %</th>
            <th className="border px-2 py-1">Quantity</th>
            <th className="border px-2 py-1">Order Type</th>
            <th className="border px-2 py-1">TIF</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((trade, index) => (
            <tr key={index} className="even:bg-gray-50">
              <td className="border px-2 py-1 text-center">
                <span onClick={() => handleActivate(index)} style={{ cursor: "pointer" }}>
                  {trade.order_status === "active" ? "✅" : "❌"}
                </span>
              </td>
              <td className="border px-2 py-1">
                <input
                  value={trade.symbol || ""}
                  onChange={(e) => handleInputChange(index, "symbol", e.target.value)}
                  className="w-full"
                />
              </td>
              <td className="border px-2 py-1 text-center">
                <span className={`px-2 py-1 rounded font-bold text-white ${trade.trade_status === "filled" ? "bg-green-600" :
                    trade.trade_status === "pending" ? "bg-red-600" :
                      "bg-gray-400"
                  }`}>
                  {trade.trade_status?.toUpperCase() || "N/A"}
                </span>
              </td>

              <td className="border px-2 py-1">
                <select
                  value={trade.direction || ""}
                  onChange={(e) => handleInputChange(index, "direction", e.target.value)}
                  className="w-full"
                >
                  <option value="">Select</option>
                  <option value="buy">Buy</option>
                  <option value="sell">Sell</option>
                </select>
              </td>
              <td className="border px-2 py-1">
                <input
                  type="number"
                  value={trade.entry_trigger || ""}
                  onChange={(e) => handleInputChange(index, "entry_trigger", parseFloat(e.target.value))}
                  className="w-full"
                />
              </td>
              <td className="border px-2 py-1">
                <select
                  value={trade.initial_stop_rule?.type || ""}
                  onChange={(e) => handleInputChange(index, "initial_stop_rule.type", e.target.value)}
                  className="w-full"
                >
                  <option value="">None</option>
                  <option value="custom">Custom</option>
                </select>
              </td>
              <td className="border px-2 py-1">
                <input
                  type="number"
                  value={trade.initial_stop_rule?.price || ""}
                  onChange={(e) => handleInputChange(index, "initial_stop_rule.price", parseFloat(e.target.value))}
                  className="w-full"
                />
              </td>
              <td className="border px-2 py-1">
                <select
                  value={trade.trailing_stop?.type || ""}
                  onChange={(e) => handleInputChange(index, "trailing_stop.type", e.target.value)}
                  className="w-full"
                >
                  <option value="">None</option>
                  <option value="custom">Custom</option>
                </select>
              </td>
              <td className="border px-2 py-1">
                <input
                  type="number"
                  value={trade.trailing_stop?.price || ""}
                  onChange={(e) => handleInputChange(index, "trailing_stop.price", parseFloat(e.target.value))}
                  className="w-full"
                />
              </td>
              <td className="border px-2 py-1">
                <input
                  type="number"
                  value={trade.portfolio_value || ""}
                  onChange={(e) => handleInputChange(index, "portfolio_value", parseFloat(e.target.value))}
                  className="w-full"
                />
              </td>
              <td className="border px-2 py-1">
                <input
                  type="number"
                  value={trade.risk_pct || ""}
                  onChange={(e) => handleInputChange(index, "risk_pct", parseFloat(e.target.value))}
                  className="w-full"
                />
              </td>
              <td className="border px-2 py-1 text-center">{trade.quantity || ""}</td>
              <td className="border px-2 py-1">
                <select
                  value={trade.order_type || ""}
                  onChange={(e) => handleInputChange(index, "order_type", e.target.value)}
                  className="w-full"
                >
                  <option value="">Select</option>
                  <option value="market">Market</option>
                  <option value="limit">Limit</option>
                </select>
              </td>
              <td className="border px-2 py-1">
                <select
                  value={trade.time_in_force || ""}
                  onChange={(e) => handleInputChange(index, "time_in_force", e.target.value)}
                  className="w-full"
                >
                  <option value="">Select</option>
                  <option value="GTC">GTC</option>
                  <option value="DAY">DAY</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody> 
    </table>
    <div className="mt-6 text-center text-base italic text-gray-600 border-t pt-4">
      “Whenever I enter a position, I have a predetermined stop. That is the only way I can sleep.
      I know where I'm getting out before I get in. The position size on a trade is determined by the stop,
      and the stop is determined on a technical basis.” — <span className="font-medium">Bruce Kovner</span>
  </div>
</div>  
);
}

export default App;
