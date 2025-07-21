import React from "react";

const PortfolioPanel = ({ portfolio, updatePortfolio, liveRisk, livePnl, buyingPower, safeToFixed }) => {
  const netRisk = portfolio.use_pnl_offset === "Yes" ? liveRisk + livePnl : liveRisk;

  return (
    <div className="mb-6 bg-dark-panel border border-gray-700 rounded p-4 w-[320px] shadow-lg">
      <h2 className="text-md font-bold mb-2 text-white">Portfolio</h2>
      <div className="flex flex-col gap-1">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-300">PortfolioValue</span>
          <input
            type="text"
            className="bg-dark-input border border-gray-600 px-2 py-1 rounded w-28 text-right text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={new Intl.NumberFormat("en-US", {
              style: "currency",
              currency: "USD",
              minimumFractionDigits: 0,
              maximumFractionDigits: 0
            }).format(portfolio["portfolio_value"] || 0)}
            onChange={(e) => {
              const cleaned = e.target.value.replace(/[^0-9]/g, "");
              updatePortfolio("portfolio_value", Number(cleaned));
            }}
          />
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-300">LiveRisk</span>
          <input
            type="text"
            className={`bg-gray-700 border border-gray-600 px-2 py-1 rounded w-28 text-right cursor-not-allowed font-semibold ${liveRisk > 0 ? "text-red-400" : "text-gray-400"}`}
            value={new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(liveRisk)}
            disabled
          />
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-300">LivePNL</span>
          <input
            type="text"
            className={`bg-gray-700 border border-gray-600 px-2 py-1 rounded w-28 text-right cursor-not-allowed font-semibold ${livePnl >= 0 ? "text-green-400" : "text-red-400"}`}
            value={`${livePnl >= 0 ? "+" : "-"}${new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(Math.abs(livePnl))}`}
            disabled
          />
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-300">UsePNLOffset</span>
          <select
            className="bg-dark-input border border-gray-600 px-2 py-1 rounded w-28 text-right text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={portfolio.use_pnl_offset}
            onChange={(e) => updatePortfolio("use_pnl_offset", e.target.value)}
          >
            <option value="Yes">Yes</option>
            <option value="No">No</option>
          </select>
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-300">NetRisk</span>
          <input
            type="text"
            className="bg-gray-700 border border-gray-600 px-2 py-1 rounded w-28 text-right cursor-not-allowed font-semibold text-gray-400"
            value={new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(netRisk)}
            disabled
          />
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-300">MaxRisk</span>
          <input
            type="text"
            className={`bg-dark-input border border-gray-600 px-2 py-1 rounded w-28 text-right focus:outline-none focus:ring-2 focus:ring-blue-500 ${portfolio.max_risk > 0 ? "text-red-400 font-semibold" : "text-gray-400"}`}
            value={new Intl.NumberFormat("en-US", {
              style: "currency",
              currency: "USD",
              minimumFractionDigits: 0,
              maximumFractionDigits: 0
            }).format(portfolio.max_risk || 0)}
            onChange={(e) => {
              const cleaned = e.target.value.replace(/[^0-9]/g, "");
              updatePortfolio("max_risk", Number(cleaned));
            }}
          />
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-300">BuyingPower</span>
          <input
            type="text"
            className="bg-gray-700 border border-gray-600 px-2 py-1 rounded w-28 text-right cursor-not-allowed font-semibold text-gray-400"
            value={new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(buyingPower)}
            disabled
          />
        </div>
      </div>
    </div>
  );
};

export default PortfolioPanel;
