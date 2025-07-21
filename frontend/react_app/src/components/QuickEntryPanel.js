import React from "react";

const QuickEntryPanel = ({ trade = {} }) => (
  <div className="bg-dark-panel border border-gray-700 rounded p-4 w-[220px] shadow-lg">
    <h2 className="text-md font-bold mb-2 text-white">Quick Entry</h2>
    <div className="flex flex-col gap-1 text-sm">
      <div className="flex justify-between items-center">
        <span className="text-gray-300">Symbol</span>
        <input
          type="text"
          className="bg-gray-700 border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-400 cursor-not-allowed"
          value={trade.symbol ?? "--"}
          disabled
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-300">Side</span>
        <input
          type="text"
          className="bg-gray-700 border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-400 cursor-not-allowed"
          value={trade.direction ?? "--"}
          disabled
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-300">Quantity</span>
        <input
          type="text"
          className="bg-gray-700 border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-400 cursor-not-allowed"
          value={trade.calculated_quantity ?? "--"}
          disabled
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-300">Price</span>
        <input
          type="text"
          className="bg-gray-700 border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-400 cursor-not-allowed"
          value={trade.entry_rules?.[0]?.value ?? "--"}
          disabled
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-300">Stop Loss</span>
        <input
          type="text"
          className="bg-gray-700 border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-400 cursor-not-allowed"
          value={trade.initial_stop_rules?.[0]?.value ?? "--"}
          disabled
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-300">Take Profit</span>
        <input
          type="text"
          className="bg-gray-700 border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-400 cursor-not-allowed"
          value={trade.take_profit_rules?.[0]?.value ?? "--"}
          disabled
        />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-300">Risk Amount</span>
        <input
          type="text"
          className="bg-gray-700 border border-gray-600 px-2 py-1 rounded w-20 text-right text-gray-400 cursor-not-allowed"
          value={trade.usd_risk ?? "--"}
          disabled
        />
      </div>
    </div>
  </div>
);

export default QuickEntryPanel; 