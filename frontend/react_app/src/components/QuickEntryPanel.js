import React from "react";

const QuickEntryPanel = ({ trade = {} }) => (
  <div className="border border-gray-300 rounded p-4 w-[220px]">
    <h2 className="text-md font-semibold mb-2 text-gray-700">Quick Entry</h2>
    <div className="flex flex-col gap-1 text-sm">
      <div className="flex justify-between items-center">
        <span className="text-gray-700">Symbol</span>
        <input
          type="text"
          className="border px-2 py-1 rounded w-20 text-right bg-gray-100 cursor-not-allowed text-gray-500"
          value={trade.symbol ?? "--"}
          disabled
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-700">Side</span>
        <input
          type="text"
          className="border px-2 py-1 rounded w-20 text-right bg-gray-100 cursor-not-allowed text-gray-500"
          value={trade.direction ?? "--"}
          disabled
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-700">Quantity</span>
        <input
          type="text"
          className="border px-2 py-1 rounded w-20 text-right bg-gray-100 cursor-not-allowed text-gray-500"
          value={trade.calculated_quantity ?? "--"}
          disabled
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-700">Price</span>
        <input
          type="text"
          className="border px-2 py-1 rounded w-20 text-right bg-gray-100 cursor-not-allowed text-gray-500"
          value={trade.entry_rules?.[0]?.value ?? "--"}
          disabled
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-700">Stop Loss</span>
        <input
          type="text"
          className="border px-2 py-1 rounded w-20 text-right bg-gray-100 cursor-not-allowed text-gray-500"
          value={trade.initial_stop_rules?.[0]?.value ?? "--"}
          disabled
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-700">Take Profit</span>
        <input
          type="text"
          className="border px-2 py-1 rounded w-20 text-right bg-gray-100 cursor-not-allowed text-gray-500"
          value={trade.take_profit_rules?.[0]?.value ?? "--"}
          disabled
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-700">Risk Amount</span>
        <input
          type="text"
          className="border px-2 py-1 rounded w-20 text-right bg-gray-100 cursor-not-allowed text-gray-500"
          value={trade.usd_risk ?? "--"}
          disabled
        />
      </div>
    </div>
  </div>
);

export default QuickEntryPanel; 