import React from "react";

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

const TradeTable = ({ trades, layout, handleInputChange, getAllFields, numericFields, lookupTicker, setTrades, selectedTradeIndex, onSelectTrade }) => {
  const formatOrderStatus = (status) => {
    const normalized = (status || "").toLowerCase();

    const pillStyles = {
      "inactive": "bg-gray-400 text-white",
      "Working": "bg-blue-500 text-white",
      "entry order submitted": "bg-yellow-500 text-black",
      "contingent order active": "bg-indigo-600 text-white",
      "contingent order submitted": "bg-purple-600 text-white",
    };

    const labelMap = {
      "inactive": "Inactive",
      "Working": "Working",
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

  // Dedicated handler for symbol lookup
  const handleSymbolLookup = async (index, value) => {
    const result = await lookupTicker(value);
    if (result) {
      // Always use longName as name if available
      if (result.longName) result.name = result.longName;
      const updatedTrade = { ...trades[index] };
      Object.keys(result).forEach((k) => {
        if (k.includes(".")) {
          const [parentKey, childKey] = k.split(".");
          updatedTrade[parentKey] = {
            ...(updatedTrade[parentKey] || {}),
            [childKey]: result[k],
          };
        } else {
          updatedTrade[k] = result[k];
        }
      });
      const updated = [...trades];
      updated[index] = updatedTrade;
      setTrades(updated);
    }
  };

  return (
    <div className="overflow-x-auto bg-dark-panel rounded-lg p-4 shadow-lg">
      <table className="table-auto border-collapse text-sm mt-4 w-full">
        <thead>
          <tr className="bg-gray-700 text-xs text-gray-300 uppercase">
            <th className="border border-gray-600 px-2 py-1 whitespace-nowrap">Trade #</th>
            {layout.map((section) => (
              <th
                key={section.section}
                className="border border-gray-600 px-2 py-1 text-center whitespace-nowrap"
                colSpan={section.fields.length}
              >
                {section.section}
              </th>
            ))}
          </tr>

          <tr className="bg-gray-800 text-xs text-gray-400">
            <th className="border border-gray-600 px-2 py-1 whitespace-nowrap"></th>
            {layout.flatMap((section) =>
              section.fields.map((field) => (
                <th key={field.key} className="border border-gray-600 px-2 py-1 text-left whitespace-nowrap">{field.label}</th>
              ))
            )}
          </tr>
        </thead>

        <tbody>
          {trades.map((trade, index) => (
            <tr
              key={`trade-${index}`}
              className={`even:bg-gray-800/50 cursor-pointer hover:bg-gray-700/50 transition-colors ${selectedTradeIndex === index ? 'bg-blue-900/50' : ''}`}
              onClick={() => onSelectTrade(index)}
            >
              <td className="border border-gray-600 px-2 py-1 font-semibold text-gray-300 whitespace-nowrap">Trade {index + 1}</td>
              {layout.flatMap((section) =>
                section.fields.map((field) => {
                  const flatTrade = flattenToFlat(trade);
                  let value;
                  if (field.key === "trade_date") {
                    value = trade.filled_at
                      ? new Date(trade.filled_at).toLocaleString("en-AU", {
                          timeZone: "Australia/Sydney",
                          day: "2-digit",
                          month: "short",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit"
                        })
                      : "--";
                  } else if (field.key === "filled_quantity") {
                    value = trade.filled_qty ?? "--";
                  } else if (field.key === "fill_price") {
                    value = typeof trade.executed_price === "number"
                      ? `$${trade.executed_price.toFixed(2)}`
                      : "--";
                  } else {
                    value = flatTrade[field.key] ?? "";
                  }

                  const handleChange = (newValue) => {
                      handleInputChange(index, field.key, newValue, trades);
                  };

                  // Special handling for rule value fields
                  if (["entry_rules.0.value", "initial_stop_rules.0.value", "trailing_stop_rules.0.value", "take_profit_rules.0.value"].includes(field.key)) {
                    // Determine the secondary source for this rule
                    let secondarySource = "";
                    if (field.key === "entry_rules.0.value") secondarySource = flatTrade["entry_rules.0.secondary_source"];
                    if (field.key === "initial_stop_rules.0.value") secondarySource = flatTrade["initial_stop_rules.0.secondary_source"];
                    if (field.key === "trailing_stop_rules.0.value") secondarySource = flatTrade["trailing_stop_rules.0.secondary_source"];
                    if (field.key === "take_profit_rules.0.value") secondarySource = flatTrade["take_profit_rules.0.secondary_source"];
                    const isCustom = secondarySource === "Custom";
                    return (
                      <td key={`${field.key}-${index}`} className="border border-gray-600 px-2 py-1 whitespace-nowrap">
                        <input
                          type="number"
                          value={value ?? ""}
                          disabled={!isCustom || !trade.editing}
                          onChange={e => isCustom && trade.editing && handleChange(e.target.value)}
                          className={`px-1 text-sm border rounded max-w-[120px] ${(!isCustom || !trade.editing) ? "bg-gray-700 border-gray-600 text-gray-400 cursor-not-allowed" : "bg-dark-input border-gray-600 text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"}`}
                        />
                      </td>
                    );
                  }

                  return (
                    <td key={`${field.key}-${index}`} className="border border-gray-600 px-2 py-1 whitespace-nowrap">
                      {field.key === "symbol" ? (
                        <input
                          type="text"
                          value={String(value || "")}
                          disabled={!trade.editing}
                          onChange={(e) => handleChange(e.target.value)}
                          onBlur={() => handleSymbolLookup(index, value)}
                          onKeyDown={e => {
                            if ((e.key === "Enter" || e.key === "Tab") && trade.action !== "--") {
                              e.preventDefault();
                              handleSymbolLookup(index, value);
                            }
                          }}
                                  className={`px-1 text-sm border rounded max-w-[120px] ${!trade.editing ? "bg-gray-700 border-gray-600 text-gray-400" : "bg-dark-input border-gray-600 text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                      }`}

                        />
                      ) : field.key === "name" ? (
                        <span className="text-gray-300">{flatTrade[field.key] || "--"}</span>
                      ) : field.key === "last_price" ? (
                        <span className="text-gray-300">{flatTrade[field.key] !== undefined ? flatTrade[field.key] : "--"}</span>
                      ) : field.key === "order_status" || field.key === "trade_status" ? (
                        <div className="flex justify-center items-center">
                          {field.key === "order_status"
                            ? formatOrderStatus(trade.order_status)
                            : trade.trade_status?.toLowerCase() === "live"
                            ? <span className="bg-green-600 text-white font-bold px-2 py-1 rounded text-sm">Live</span>
                            : <span className="text-gray-400">{String(value || "--")}</span>}
                        </div>
                      ) : field.type === "select" ? (
                        <select
                          value={String(value || "")}
                          onChange={(e) => handleChange(e.target.value)}
                                      disabled={
                                          field.readonly === true ||
                                          (!trade.editing && field.key !== "action")
                                      }


                          className={`px-1 text-sm border rounded max-w-[120px] ${
                              field.readonly === true ||
                                  (!trade.editing && field.key !== "action")
                                  ? "bg-gray-700 border-gray-600 text-gray-400 cursor-not-allowed"
                                  : "bg-dark-input border-gray-600 text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"

                          }`}
                        >
                          <option value="">--</option>
                          {field.options.map((opt) => (
                            <option key={opt} value={opt}>{opt}</option>
                          ))}
                        </select>
                      ) : field.type === "checkbox" ? (
                        <input
                          type="checkbox"
                          checked={!!value}
                          onChange={(e) => handleChange(e.target.checked)}
                        />
                      ) : (
                        <input
                          type="text"
                          value={
                            field.key === "percent_at_risk"
                              ? `${safeToFixed(-1 * value)}%`
                              : field.key === "dollar_at_risk"
                                ? safeDollar(-1 * value)
                                : field.key === "pnl_percent"
                                  ? `${safeToFixed(value)}%`
                                  : field.key === "pnl_dollar"
                                    ? safeDollar(value)
                                    : field.key === "risk_pct" && !isNaN(value)
                                      ? `${value}%`
                                      : String(value || "")
                          }
                                                  disabled={
                                                      field.readonly === true ||
                                                      (!trade.editing && field.key !== "action")
                                                  }


                          onChange={(e) => {
                              if (
                                  !(field.readonly === true ||
                                      (!trade.editing && field.key !== "action"))
                              ) {

                              const rawValue = e.target.value.replace(/[^\d.]/g, "");
                              const finalValue = numericFields.has(field.key)
                                ? Number(rawValue)
                                : rawValue;
                              handleChange(finalValue);
                            }
                          }}
                          className={`px-1 text-sm border rounded max-w-[120px] ${
                              field.readonly === true ||
                                  (!trade.editing && field.key !== "action")

                              ? "bg-gray-700 border-gray-600 text-gray-400 cursor-not-allowed"
                              : "bg-dark-input border-gray-600 text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          } ${
                            ["percent_at_risk", "dollar_at_risk", "pnl_percent", "pnl_dollar"].includes(field.key) &&
                            Number(value) > 0
                              ? "text-red-400 font-semibold"
                              : "text-gray-300"
                          }`}
                        />
                      )}
                    </td>
                  );
                })
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TradeTable;
