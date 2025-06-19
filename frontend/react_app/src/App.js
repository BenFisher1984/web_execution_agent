import React, { useEffect, useState } from 'react';
import { useStatusPoll } from "./hooks/useStatusPoll";

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

  
  // 🆕 Flatten layoutConfig fields
  const getAllFields = () => {
  return layoutConfig.flatMap((section) => section.fields);
};

  useEffect(() => {
    console.log("🛠 useEffect running on mount");
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
        if (trades.length === 0) {
          console.log("🧾 Loaded trade count:", data.num_trades);
          setTrades(Array.from({ length: data.num_trades }, () => ({})));
        } else {
          console.log("⚠️ Skipping trade init — already populated");
        }
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
            setTrades(prev => [...prev, {}]);
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



      {/* Existing Trade Table Follows */}

      <table className="table-auto border-collapse w-auto text-sm">

  <thead className="bg-gray-200 text-xs text-gray-600 uppercase">
    <tr>
      <th className="border px-2 py-1 text-left">Field</th>
      {trades.map((_, i) => (
        <th key={i} className="border px-2 py-1 text-left">
          Trade {i + 1}
        </th>
      ))}
    </tr>
  </thead>
  <tbody>
  {layoutConfig.map((section) => (
    <React.Fragment key={section.section}>
      {/* Section header row */}
      <tr className="bg-gray-100">
        <td colSpan={trades.length + 1} className="px-2 py-2 font-semibold text-sm text-gray-700">
          {section.section}
        </td>
      </tr>

      {/* Field rows */}
      {section.fields.filter(field => field.enabled !== false).map((field) => (
        <tr key={field.key} className="even:bg-gray-50">
          <td className="border px-2 py-1 text-gray-800">&ndash; {field.label}</td>
          {trades.map((trade, index) => {
            const value = field.key.split('.').reduce((obj, key) => obj?.[key], trade);
            const handleChange = (newValue) => {
              handleInputChange(index, field.key, newValue);
            };

            return (
              <td key={index + field.key} className="border px-2 py-1">
                {field.type === "text" || field.type === "number" ? (
                  <input
                    type={field.type}
                    value={value || ""}
                    onChange={(e) =>
                      handleChange(field.type === "number" ? Number(e.target.value) : e.target.value)
                    }
                    className="px-1 text-sm border rounded max-w-[120px]"
                  />
                ) : field.type === "select" ? (
                  <select
                    value={value || ""}
                    onChange={(e) => handleChange(e.target.value)}
                    className="px-1 text-sm border rounded max-w-[120px]"
                  >
                    <option value="">--</option>
                    {field.options.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                ) : field.type === "checkbox" ? (
                  <input
                    type="checkbox"
                    checked={!!value}
                    onChange={(e) => handleChange(e.target.checked)}
                  />
                ) : (
                  <span>{value}</span>
                )}
              </td>
            );
          })}
        </tr>
      ))}
    </React.Fragment>
  ))}
</tbody>

</table>

{modifyLayoutMode && (
  <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
    <div className="bg-white rounded-lg shadow-lg w-[90%] max-w-4xl max-h-[90%] overflow-y-auto p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-800">Modify Layout</h2>
        <button
          onClick={() => setModifyLayoutMode(false)}
          className="text-gray-500 hover:text-gray-800"
        >
          ✖
        </button>
      </div>

      <table className="table-auto border-collapse w-full text-sm">
        <thead className="bg-gray-100">
          <tr>
            <th className="border px-2 py-1 text-left">Field</th>
            <th className="border px-2 py-1 text-left">Include?</th>
          </tr>
        </thead>
        <tbody>
          {layoutDraft.map((section) => (
            <React.Fragment key={section.section}>
              <tr className="bg-gray-50">
                <td colSpan={2} className="px-2 py-2 font-semibold text-sm text-gray-700">
                  {section.section}
                </td>
              </tr>
              {section.fields.map((field) => (
                <tr key={field.key} className="even:bg-gray-50">
                  <td className="border px-2 py-1 text-gray-800">&ndash; {field.label}</td>
                  <td className="border px-2 py-1 text-center">
                    <input
                      type="checkbox"
                      checked={field.enabled !== false}
                      onChange={(e) => {
                        const updated = layoutDraft.map((s) =>
                          s.section === section.section
                            ? {
                                ...s,
                                fields: s.fields.map((f) =>
                                  f.key === field.key
                                    ? { ...f, enabled: e.target.checked }
                                    : f
                                ),
                              }
                            : s
                        );
                        setLayoutDraft(updated);
                      }}
                    />
                  </td>
                </tr>
              ))}
            </React.Fragment>
          ))}
        </tbody>
      </table>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => {
                  fetch("http://localhost:8000/layout_config", {
                    method: "POST",
                    headers: {
                      "Content-Type": "application/json"
                    },
                    body: JSON.stringify(layoutDraft)
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

                className="bg-blue-600 text-white text-sm px-4 py-1 rounded hover:bg-blue-700"
              >
                Save Layout
              </button>
              <button
                onClick={() => setModifyLayoutMode(false)}
                className="bg-gray-300 text-sm px-4 py-1 rounded hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>

    </div>
  </div>
)}

{showDeleteModal && (
  <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
    <div className="bg-white rounded-lg shadow-lg w-[90%] max-w-md p-6">
      <h2 className="text-lg font-semibold mb-4 text-gray-800">Delete Trade</h2>
      <p className="text-sm text-gray-700 mb-2">Select a trade to delete:</p>

      <ul className="mb-4">
        {trades.map((_, index) => (
          <li key={index} className="mb-2">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="tradeToDelete"
                value={index}
                checked={tradeToDelete === index}
                onChange={() => setTradeToDelete(index)}
              />
              <span>Trade {index + 1}</span>
            </label>
          </li>
        ))}
      </ul>

      <div className="flex justify-end gap-3">
        <button
          onClick={() => {
            if (tradeToDelete !== null) {
              setTrades(prev => prev.filter((_, i) => i !== tradeToDelete));
              setTradeToDelete(null);
              setShowDeleteModal(false);
            }
          }}
          disabled={tradeToDelete === null}
          className={`text-sm px-4 py-1 rounded ${
            tradeToDelete === null
              ? "bg-gray-300 cursor-not-allowed"
              : "bg-red-600 text-white hover:bg-red-700"
          }`}
        >
          Apply
        </button>

        <button
          onClick={() => {
            setTradeToDelete(null);
            setShowDeleteModal(false);
          }}
          className="bg-gray-300 text-sm px-4 py-1 rounded hover:bg-gray-400"
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
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
