import React from "react";

const EntryRulesPanel = ({ entryRules = [], onChange }) => {
  const rule = entryRules[0] || {};
  const isCustom = rule.secondary_source === "Custom";
  return (
    <div className="border border-gray-300 rounded p-4 w-[220px]">
      <h2 className="text-md font-semibold mb-2 text-gray-700">Entry Rules</h2>
      <div className="flex flex-col gap-1 text-sm">
        <div className="flex justify-between items-center">
          <span className="text-gray-700">Primary Source</span>
          <select
            value={rule.primary_source ?? ""}
            onChange={e => onChange && onChange("entry_rules.0.primary_source", e.target.value)}
            className="border px-2 py-1 rounded w-20 text-right bg-white"
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
          <span className="text-gray-700">Condition</span>
          <select
            value={rule.condition ?? ""}
            onChange={e => onChange && onChange("entry_rules.0.condition", e.target.value)}
            className="border px-2 py-1 rounded w-20 text-right bg-white"
          >
            <option value="">--</option>
            <option value=">=">&gt;=</option>
            <option value="<=">&lt;=</option>
            <option value=">">&gt;</option>
            <option value="<">&lt;</option>
          </select>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-700">Secondary Source</span>
          <select
            value={rule.secondary_source ?? ""}
            onChange={e => onChange && onChange("entry_rules.0.secondary_source", e.target.value)}
            className="border px-2 py-1 rounded w-20 text-right bg-white"
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
          <span className="text-gray-700">Value</span>
          {isCustom ? (
            <input
              type="number"
              className="border px-2 py-1 rounded w-20 text-right bg-white"
              value={rule.value ?? ""}
              onChange={e => onChange && onChange("entry_rules.0.value", e.target.value)}
            />
          ) : (
            <input
              type="number"
              className="border px-2 py-1 rounded w-20 text-right bg-gray-100 cursor-not-allowed"
              value={rule.value ?? ""}
              disabled
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default EntryRulesPanel; 