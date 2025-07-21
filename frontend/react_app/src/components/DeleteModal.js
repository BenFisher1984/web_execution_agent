import React from "react";

const DeleteModal = ({ trades, tradeToDelete, setTradeToDelete, setShowDeleteModal, setTrades }) => {
  const handleDelete = () => {
    if (tradeToDelete !== null) {
      const updatedTrades = trades.filter((_, i) => i !== tradeToDelete);
      setTrades(updatedTrades);
      fetch("http://localhost:8000/save_trades", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedTrades),
      });
      setTradeToDelete(null);
      setShowDeleteModal(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-70 flex items-center justify-center">
      <div className="bg-dark-panel border border-gray-600 rounded-lg shadow-2xl w-[90%] max-w-md p-6">
        <h2 className="text-lg font-bold mb-4 text-white">Delete Trade</h2>
        <p className="text-sm text-gray-300 mb-2">Select a trade to delete:</p>

        <ul className="mb-4">
          {trades.map((_, index) => (
            <li key={index} className="mb-2">
              <label className="flex items-center gap-2 text-gray-300">
                <input
                  type="radio"
                  name="tradeToDelete"
                  value={index}
                  checked={tradeToDelete === index}
                  onChange={() => setTradeToDelete(index)}
                  className="accent-blue-500"
                />
                <span>Trade {index + 1}</span>
              </label>
            </li>
          ))}
        </ul>

        <div className="flex justify-end gap-3">
          <button
            onClick={handleDelete}
            disabled={tradeToDelete === null}
            className={`text-sm px-4 py-1 rounded transition-colors ${
              tradeToDelete === null
                ? "bg-gray-600 text-gray-400 cursor-not-allowed"
                : "bg-red-600 text-white hover:bg-red-700"
            }`}
          >
            Apply
          </button>

          <button
            onClick={() => {
              setTradeToDelete(null);
              setShowDeleteModal(false);
            }}
            className="bg-gray-600 text-gray-300 text-sm px-4 py-1 rounded hover:bg-gray-500 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteModal;
