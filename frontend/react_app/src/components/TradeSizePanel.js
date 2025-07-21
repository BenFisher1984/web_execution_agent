import React from "react";

const TradeSizePanel = ({ tradeSize, onChange }) => (
  <div className="bg-dark-panel border border-gray-700 rounded p-4 w-[220px] shadow-lg">
    <h2 className="text-md font-bold mb-2 text-white">Trade Size</h2>
    <div className="flex flex-col gap-1 text-sm">
      <div className="flex justify-between items-center">
        <span className="text-gray-300">Quantity</span>
        <input
          type="number"
          className="bg-dark-input border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={tradeSize?.calculated_quantity ?? ""}
          onChange={e => onChange && onChange("calculated_quantity", e.target.value)}
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-300">USD</span>
        <input
          type="number"
          className="bg-dark-input border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={tradeSize?.usd ?? ""}
          onChange={e => onChange && onChange("usd", e.target.value)}
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-300">% Balance</span>
        <input
          type="number"
          className="bg-dark-input border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={tradeSize?.percent_balance ?? ""}
          onChange={e => onChange && onChange("percent_balance", e.target.value)}
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-300">USD Risk</span>
        <input
          type="number"
          className="bg-dark-input border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={tradeSize?.usd_risk ?? ""}
          onChange={e => onChange && onChange("usd_risk", e.target.value)}
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-300">% Risk</span>
        <input
          type="number"
          className="bg-dark-input border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={tradeSize?.percent_risk ?? ""}
          onChange={e => onChange && onChange("percent_risk", e.target.value)}
        />
      </div>
    </div>
  </div>
);

export default TradeSizePanel; 