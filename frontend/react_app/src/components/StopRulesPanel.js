import React from "react";

const StopRulesPanel = ({ initialStopRules = [], onChange }) => {
  const rule = initialStopRules[0] || {};
  const isCustom = rule.secondary_source === "Custom";
  return (
    <div className="bg-dark-panel border border-gray-700 rounded p-4 w-[220px] shadow-lg">
      <h2 className="text-md font-bold mb-2 text-white">Stop Rules</h2>
      <div className="flex flex-col gap-1 text-sm">
        <div className="flex justify-between items-center">
          <span className="text-gray-300">Primary Source</span>
          <select
            value={rule.primary_source ?? ""}
            onChange={e => onChange && onChange("initial_stop_rules.0.primary_source", e.target.value)}
            className="bg-dark-input border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">--</option>
            <option value="Price">Price</option>
            <option value="EMA 8">EMA 8</option>
            <option value="SMA 8">SMA 8</option>
            <option value="EMA 21">EMA 21</option>
            <option value="SMA 21">SMA 21</option>
            <option value="ADR">ADR</option>
            <option value="ATR">ATR</option>
            <option value="Custom">Custom</option>
          </select>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-300">Condition</span>
          <select
            value={rule.condition ?? ""}
            onChange={e => onChange && onChange("initial_stop_rules.0.condition", e.target.value)}
            className="bg-dark-input border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">--</option>
            <option value=">=">&gt;=</option>
            <option value="<=">&lt;=</option>
            <option value=">">&gt;</option>
            <option value="<">&lt;</option>
          </select>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-300">Secondary Source</span>
          <select
            value={rule.secondary_source ?? ""}
            onChange={e => onChange && onChange("initial_stop_rules.0.secondary_source", e.target.value)}
            className="bg-dark-input border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">--</option>
            <option value="Price">Price</option>
            <option value="EMA 8">EMA 8</option>
            <option value="SMA 8">SMA 8</option>
            <option value="EMA 21">EMA 21</option>
            <option value="SMA 21">SMA 21</option>
            <option value="ADR">ADR</option>
            <option value="ATR">ATR</option>
            <option value="Custom">Custom</option>
          </select>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-300">Value</span>
          {isCustom ? (
            <input
              type="number"
              className="bg-dark-input border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={rule.value ?? ""}
              onChange={e => onChange && onChange("initial_stop_rules.0.value", e.target.value)}
            />
          ) : (
            <input
              type="number"
              className="bg-gray-700 border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-400 cursor-not-allowed"
              value={rule.value ?? ""}
              disabled
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default StopRulesPanel; 