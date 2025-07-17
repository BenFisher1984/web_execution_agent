import React from "react";

const PortfolioPanel = ({ portfolio, updatePortfolio, liveRisk, livePnl, buyingPower, safeToFixed }) => {
  const netRisk = portfolio.use_pnl_offset === "Yes" ? liveRisk + livePnl : liveRisk;

  return (
    <div className="mb-6 border border-gray-300 rounded p-4 w-[320px]">
      <h2 className="text-md font-semibold mb-2 text-gray-700">Portfolio</h2>
      <div className="flex flex-col gap-1">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-700">PortfolioValue</span>
          <input
            type="text"
            className="border px-2 py-1 rounded w-28 text-right"
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
          <span className="text-gray-700">LiveRisk</span>
          <input
            type="text"
            className={`border px-2 py-1 rounded w-28 text-right bg-gray-100 cursor-not-allowed font-semibold ${liveRisk > 0 ? "text-red-600" : "text-gray-600"}`}
            value={new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(liveRisk)}
            disabled
          />
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-700">LivePNL</span>
          <input
            type="text"
            className={`border px-2 py-1 rounded w-28 text-right bg-gray-100 cursor-not-allowed font-semibold ${livePnl >= 0 ? "text-green-600" : "text-red-600"}`}
            value={`${livePnl >= 0 ? "+" : "-"}${new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(Math.abs(livePnl))}`}
            disabled
          />
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-700">UsePNLOffset</span>
          <select
            className="border px-2 py-1 rounded w-28 text-right"
            value={portfolio.use_pnl_offset}
            onChange={(e) => updatePortfolio("use_pnl_offset", e.target.value)}
          >
            <option value="Yes">Yes</option>
            <option value="No">No</option>
          </select>
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-700">NetRisk</span>
          <input
            type="text"
            className="border px-2 py-1 rounded w-28 text-right bg-gray-100 cursor-not-allowed font-semibold text-gray-600"
            value={new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(netRisk)}
            disabled
          />
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-700">MaxRisk</span>
          <input
            type="text"
            className={`border px-2 py-1 rounded w-28 text-right ${portfolio.max_risk > 0 ? "text-red-600 font-semibold" : "text-gray-600"}`}
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
          <span className="text-gray-700">BuyingPower</span>
          <input
            type="text"
            className="border px-2 py-1 rounded w-28 text-right bg-gray-100 cursor-not-allowed font-semibold text-gray-600"
            value={new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(buyingPower)}
            disabled
          />
        </div>
      </div>
    </div>
  );
};

export default PortfolioPanel;
