// src/hooks/useTickerLookup.js

export const useTickerLookup = () => {
  const lookupTicker = async (symbol) => {
    try {
      const response = await fetch(`http://localhost:8000/ticker/${symbol.toUpperCase()}`);
      if (!response.ok) throw new Error("Failed to fetch ticker info");
      const data = await response.json();
      return data;
    } catch (error) {
      console.warn("⚠️ Ticker lookup failed:", error.message);
      return null;
    }
  };

  return { lookupTicker };
};
