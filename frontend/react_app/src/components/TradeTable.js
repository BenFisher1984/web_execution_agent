import React from "react";

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

const TradeTable = ({ trades, layout, handleInputChange, getAllFields, numericFields, lookupTicker }) => {
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

  return (
    <table className="table-auto border-collapse text-sm w-full mt-4">
      <thead>
        <tr className="bg-gray-200 text-xs text-gray-700 uppercase">
          <th className="border px-2 py-1">Trade #</th>
          {layout.map((section) => (
            <th
              key={section.section}
              className="border px-2 py-1 text-center"
              colSpan={section.fields.length}
            >
              {section.section}
            </th>
          ))}
        </tr>

        <tr className="bg-gray-100 text-xs text-gray-600">
          <th className="border px-2 py-1"></th>
          {layout.flatMap((section) =>
            section.fields.map((field) => (
              <th key={field.key} className="border px-2 py-1 text-left">{field.label}</th>
            ))
          )}
        </tr>
      </thead>

      <tbody>
        {trades.map((trade, index) => (
          <tr key={`trade-${index}`} className="even:bg-gray-50">
            <td className="border px-2 py-1 font-semibold text-gray-800">Trade {index + 1}</td>
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


                return (
                  <td key={`${field.key}-${index}`} className="border px-2 py-1">
                    {field.key === "symbol" ? (
                      <input
                        type="text"
                        value={String(value || "")}
                        disabled={!trade.editing}
                        onChange={(e) => handleChange(e.target.value)}
                        onBlur={async () => {
                          if (!value || trade.action === "--") return;
                          const result = await lookupTicker(value);
                          if (result) {
                            Object.keys(result).forEach((k) => {
                              if (getAllFields().some((f) => f.key === k)) {
                                const rawVal = result[k];
                                const casted = numericFields.has(k) ? Number(rawVal) : rawVal;
                                handleInputChange(index, k, casted, trades);
                              }
                            });
                          }
                        }}
                        onKeyDown={async (e) => {
                          if ((e.key === "Enter" || e.key === "Tab") && trade.action !== "--") {
                            e.preventDefault();
                            if (!value) return;
                            const result = await lookupTicker(value);
                            if (result) {
                              Object.keys(result).forEach((k) => {
                                if (getAllFields().some((f) => f.key === k)) {
                                  const rawVal = result[k];
                                  const casted = numericFields.has(k) ? Number(rawVal) : rawVal;
                                  handleInputChange(index, k, casted, trades);
                                }
                              });
                            }
                          }
                        }}
                                className={`px-1 text-sm border rounded max-w-[120px] ${!trade.editing ? "bg-gray-100" : "bg-white"
                                    }`}

                      />
                    ) : field.key === "order_status" || field.key === "trade_status" ? (
                      <div className="flex justify-center items-center">
                        {field.key === "order_status"
                          ? formatOrderStatus(trade.order_status)
                          : trade.trade_status?.toLowerCase() === "live"
                          ? <span className="bg-green-600 text-white font-bold px-2 py-1 rounded text-sm">Live</span>
                          : <span className="text-gray-700">{String(value || "--")}</span>}
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
                                ? "bg-gray-100 cursor-not-allowed"
                                : "bg-white"

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

                            ? "bg-gray-100 cursor-not-allowed"
                            : "bg-white"
                        } ${
                          ["percent_at_risk", "dollar_at_risk", "pnl_percent", "pnl_dollar"].includes(field.key) &&
                          Number(value) > 0
                            ? "text-red-600 font-semibold"
                            : "text-gray-500"
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
  );
};

export default TradeTable;
