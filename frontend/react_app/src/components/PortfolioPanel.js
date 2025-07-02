import React from "react";

const PortfolioPanel = ({ portfolio, updatePortfolio, liveRisk, livePnl, buyingPower, safeToFixed }) => {
  const netRisk = portfolio.use_pnl_offset === "Yes" ? liveRisk + livePnl : liveRisk;

  return (
    <div className="mb-6 border border-gray-300 rounded p-4 w-[960px]">
      <h2 className="text-md font-semibold mb-2 text-gray-700">Portfolio</h2>
      <table className="table-auto w-full text-sm">
        <thead>
          <tr className="bg-gray-100 text-left text-xs text-gray-600">
            <th className="px-2 py-1">Portfolio Value</th>
            <th className="px-2 py-1">Live Risk</th>
            <th className="px-2 py-1">Live PNL</th>
            <th className="px-2 py-1">Use PNL Offset</th>
            <th className="px-2 py-1">Net Risk</th>
            <th className="px-2 py-1">Max Risk</th>
            <th className="px-2 py-1">Buying Power</th>
          </tr>
        </thead>
        <tbody>
          <tr className="bg-white">
            <td className="px-2 py-1">
              <input
                type="text"
                className="border px-2 py-1 rounded w-full text-right"
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
            </td>
            <td className={`px-2 py-1 bg-gray-100 ${liveRisk > 0 ? "text-red-600 font-semibold" : "text-gray-600"}`}>
              {(-1 * liveRisk).toFixed(2)}%
            </td>
            <td className="px-2 py-1 text-gray-600 bg-gray-100">{safeToFixed(livePnl)}%</td>
            <td className="px-2 py-1">
              <select
                className="border px-2 py-1 rounded w-full"
                value={portfolio.use_pnl_offset}
                onChange={(e) => updatePortfolio("use_pnl_offset", e.target.value)}
              >
                <option value="Yes">Yes</option>
                <option value="No">No</option>
              </select>
            </td>
            <td className="px-2 py-1 text-gray-600 bg-gray-100">{safeToFixed(netRisk)}%</td>
            <td className="px-2 py-1 bg-gray-100">
              <input
                type="text"
                className={`border px-2 py-1 rounded w-full text-right ${
                  portfolio.max_risk > 0 ? "text-red-600 font-semibold" : "text-gray-600"
                }`}
                value={`${(-1 * portfolio.max_risk).toFixed(2)}%`}
                onChange={(e) => {
                  const cleaned = e.target.value.replace(/[^\d.]/g, "");
                  updatePortfolio("max_risk", Number(cleaned));
                }}
              />
            </td>
            <td className="px-2 py-1 text-gray-600 bg-gray-100">{Number(buyingPower).toFixed(2)}%</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};

export default PortfolioPanel;
