import React from "react";

const TradeSizePanel = ({ tradeSize, onChange }) => (
  <div className="border border-gray-300 rounded p-4 w-[220px]">
    <h2 className="text-md font-semibold mb-2 text-gray-700">Trade Size</h2>
    <div className="flex flex-col gap-1 text-sm">
      <div className="flex justify-between items-center">
        <span className="text-gray-700">Quantity</span>
        <input
          type="number"
          className="border px-2 py-1 rounded w-20 text-right bg-white"
          value={tradeSize?.calculated_quantity ?? ""}
          onChange={e => onChange && onChange("calculated_quantity", e.target.value)}
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-700">USD</span>
        <input
          type="number"
          className="border px-2 py-1 rounded w-20 text-right bg-white"
          value={tradeSize?.usd ?? ""}
          onChange={e => onChange && onChange("usd", e.target.value)}
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-700">% Balance</span>
        <input
          type="number"
          className="border px-2 py-1 rounded w-20 text-right bg-white"
          value={tradeSize?.percent_balance ?? ""}
          onChange={e => onChange && onChange("percent_balance", e.target.value)}
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-700">USD Risk</span>
        <input
          type="number"
          className="border px-2 py-1 rounded w-20 text-right bg-white"
          value={tradeSize?.usd_risk ?? ""}
          onChange={e => onChange && onChange("usd_risk", e.target.value)}
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-700">% Risk</span>
        <input
          type="number"
          className="border px-2 py-1 rounded w-20 text-right bg-white"
          value={tradeSize?.percent_risk ?? ""}
          onChange={e => onChange && onChange("percent_risk", e.target.value)}
        />
      </div>
    </div>
  </div>
);

export default TradeSizePanel; 