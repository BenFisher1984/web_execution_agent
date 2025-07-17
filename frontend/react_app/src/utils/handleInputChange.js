export const createHandleInputChange = ({
  getAllFields,
  calculateQuantity,
  setTrades,
  portfolio,
  flattenToFlat,
  flattenToNested,
  handleActivate
}) => {
  return async function handleInputChange(index, field, value, trades) {
    const updated = [...trades];
    const trade = { ...trades[index] }; // Always start from the latest state
    const accountBalance = portfolio.portfolio_value || 0;
    // Get entry price and stop loss for this trade
    const flatTrade = flattenToFlat(trade);
    const entryPrice = Number(flatTrade["entry_rules.0.value"] || flatTrade["entry_price"] || 0);
    const stopLoss = Number(flatTrade["initial_stop_rules.0.value"] || flatTrade["initial_stop_rules.0.stop_price"] || 0);
    const direction = (flatTrade["direction"] || "").toLowerCase();

    // Helper: absolute difference for risk per share
    const riskPerShare = entryPrice && stopLoss ? Math.abs(entryPrice - stopLoss) : 0;

    // Trade size fields
    let calculated_quantity = Number(flatTrade["calculated_quantity"] || 0);
    let usd = Number(flatTrade["usd"] || 0);
    let percent_balance = Number(flatTrade["percent_balance"] || 0);
    let usd_risk = Number(flatTrade["usd_risk"] || 0);
    let percent_risk = Number(flatTrade["percent_risk"] || 0);

    // Set the edited field
    switch (field) {
      case "calculated_quantity":
        calculated_quantity = Number(value);
        usd = entryPrice ? calculated_quantity * entryPrice : 0;
        percent_balance = accountBalance ? (usd / accountBalance) * 100 : 0;
        usd_risk = riskPerShare ? calculated_quantity * riskPerShare : 0;
        percent_risk = accountBalance ? (usd_risk / accountBalance) * 100 : 0;
        break;
      case "usd":
        usd = Number(value);
        calculated_quantity = entryPrice ? usd / entryPrice : 0;
        percent_balance = accountBalance ? (usd / accountBalance) * 100 : 0;
        usd_risk = riskPerShare ? calculated_quantity * riskPerShare : 0;
        percent_risk = accountBalance ? (usd_risk / accountBalance) * 100 : 0;
        break;
      case "percent_balance":
        percent_balance = Number(value);
        usd = (percent_balance / 100) * accountBalance;
        calculated_quantity = entryPrice ? usd / entryPrice : 0;
        usd_risk = riskPerShare ? calculated_quantity * riskPerShare : 0;
        percent_risk = accountBalance ? (usd_risk / accountBalance) * 100 : 0;
        break;
      case "usd_risk":
        usd_risk = Number(value);
        calculated_quantity = riskPerShare ? usd_risk / riskPerShare : 0;
        usd = entryPrice ? calculated_quantity * entryPrice : 0;
        percent_balance = accountBalance ? (usd / accountBalance) * 100 : 0;
        percent_risk = accountBalance ? (usd_risk / accountBalance) * 100 : 0;
        break;
      case "percent_risk":
        percent_risk = Number(value);
        usd_risk = (percent_risk / 100) * accountBalance;
        calculated_quantity = riskPerShare ? usd_risk / riskPerShare : 0;
        usd = entryPrice ? calculated_quantity * entryPrice : 0;
        percent_balance = accountBalance ? (usd / accountBalance) * 100 : 0;
        break;
      case "entry_rules.0.value":
      case "entry_rules.0.secondary_source":
      case "entry_rules.0.primary_source":
      case "entry_rules.0.condition":
        if (!Array.isArray(trade.entry_rules)) trade.entry_rules = [{}];
        trade.entry_rules[0] = {
          ...trade.entry_rules[0],
          [field.split(".")[2]]: value,
        };
        updated[index] = trade;
        
        // If entry price changed, recalculate Trade Size fields
        if (field === "entry_rules.0.value") {
          const newFlatTrade = flattenToFlat(trade);
          const newEntryPrice = Number(value || 0);
          const newStopLoss = Number(newFlatTrade["initial_stop_rules.0.value"] || 0);
          const newRiskPerShare = newEntryPrice && newStopLoss ? Math.abs(newEntryPrice - newStopLoss) : 0;
          
          // Recalculate based on existing risk values (prioritize usd_risk, then percent_risk)
          const currentUsdRisk = Number(newFlatTrade["usd_risk"] || 0);
          const currentPercentRisk = Number(newFlatTrade["percent_risk"] || 0);
          
          if (newRiskPerShare > 0) {
            let newQuantity = 0;
            if (currentUsdRisk > 0) {
              newQuantity = Math.round(currentUsdRisk / newRiskPerShare);
            } else if (currentPercentRisk > 0 && accountBalance > 0) {
              const calculatedUsdRisk = (currentPercentRisk / 100) * accountBalance;
              newQuantity = Math.round(calculatedUsdRisk / newRiskPerShare);
            }
            
            if (newQuantity > 0) {
              trade["calculated_quantity"] = newQuantity;
              trade["usd"] = newEntryPrice ? Math.round(newQuantity * newEntryPrice) : 0;
              trade["percent_balance"] = accountBalance ? Number(((trade["usd"] / accountBalance) * 100).toFixed(2)) : 0;
              trade["usd_risk"] = Math.round(newQuantity * newRiskPerShare);
              trade["percent_risk"] = accountBalance ? Number(((trade["usd_risk"] / accountBalance) * 100).toFixed(2)) : 0;
              updated[index] = trade;
            }
          }
        }
        
        setTrades([...updated]);
        return;
      case "initial_stop_rules.0.value":
      case "initial_stop_rules.0.secondary_source":
      case "initial_stop_rules.0.primary_source":
      case "initial_stop_rules.0.condition":
        if (!Array.isArray(trade.initial_stop_rules)) trade.initial_stop_rules = [{}];
        trade.initial_stop_rules[0] = {
          ...trade.initial_stop_rules[0],
          [field.split(".")[2]]: value,
        };
        updated[index] = trade;
        
        // If stop price changed, recalculate Trade Size fields
        if (field === "initial_stop_rules.0.value") {
          const newFlatTrade = flattenToFlat(trade);
          const newEntryPrice = Number(newFlatTrade["entry_rules.0.value"] || 0);
          const newStopLoss = Number(value || 0);
          const newRiskPerShare = newEntryPrice && newStopLoss ? Math.abs(newEntryPrice - newStopLoss) : 0;
          
          // Recalculate based on existing risk values (prioritize usd_risk, then percent_risk)
          const currentUsdRisk = Number(newFlatTrade["usd_risk"] || 0);
          const currentPercentRisk = Number(newFlatTrade["percent_risk"] || 0);
          
          if (newRiskPerShare > 0) {
            let newQuantity = 0;
            if (currentUsdRisk > 0) {
              newQuantity = Math.round(currentUsdRisk / newRiskPerShare);
            } else if (currentPercentRisk > 0 && accountBalance > 0) {
              const calculatedUsdRisk = (currentPercentRisk / 100) * accountBalance;
              newQuantity = Math.round(calculatedUsdRisk / newRiskPerShare);
            }
            
            if (newQuantity > 0) {
              trade["calculated_quantity"] = newQuantity;
              trade["usd"] = newEntryPrice ? Math.round(newQuantity * newEntryPrice) : 0;
              trade["percent_balance"] = accountBalance ? Number(((trade["usd"] / accountBalance) * 100).toFixed(2)) : 0;
              trade["usd_risk"] = Math.round(newQuantity * newRiskPerShare);
              trade["percent_risk"] = accountBalance ? Number(((trade["usd_risk"] / accountBalance) * 100).toFixed(2)) : 0;
              updated[index] = trade;
            }
          }
        }
        
        setTrades([...updated]);
        return;
      case "trailing_stop_rules.0.value":
      case "trailing_stop_rules.0.secondary_source":
      case "trailing_stop_rules.0.primary_source":
      case "trailing_stop_rules.0.condition":
        if (!Array.isArray(trade.trailing_stop_rules)) trade.trailing_stop_rules = [{}];
        trade.trailing_stop_rules[0] = {
          ...trade.trailing_stop_rules[0],
          [field.split(".")[2]]: value,
        };
        updated[index] = trade;
        setTrades([...updated]);
        return;
      case "take_profit_rules.0.value":
      case "take_profit_rules.0.secondary_source":
      case "take_profit_rules.0.primary_source":
      case "take_profit_rules.0.condition":
        if (!Array.isArray(trade.take_profit_rules)) trade.take_profit_rules = [{}];
        trade.take_profit_rules[0] = {
          ...trade.take_profit_rules[0],
          [field.split(".")[2]]: value,
        };
        updated[index] = trade;
        setTrades([...updated]);
        return;
      default: {
        // Always set the value, even if not in layout config
        let valueToSet = value;
        const fieldDef = getAllFields().find((f) => f.key === field);
        if (fieldDef && fieldDef.type === "number") {
          valueToSet = Number(value);
        }
        if (field.includes(".")) {
          const [parentKey, childKey] = field.split(".");
          trade[parentKey] = {
            ...(trade[parentKey] || {}),
            [childKey]: valueToSet,
          };
        } else {
          trade[field] = valueToSet;
        }
        updated[index] = trade;
        setTrades([...updated]);
        // Patch: If action is set to 'Activate', trigger handleActivate
        if (field === "action" && valueToSet === "Activate" && typeof handleActivate === "function") {
          await handleActivate(index);
        }
        return;
      }
    }

    // Update the trade with calculated values
    trade["calculated_quantity"] = Math.round(calculated_quantity) || 0;
    trade["usd"] = Math.round(usd) || 0;
    trade["percent_balance"] = Number(percent_balance.toFixed(2)) || 0;
    trade["usd_risk"] = Math.round(usd_risk) || 0;
    trade["percent_risk"] = Number(percent_risk.toFixed(2)) || 0;
    updated[index] = trade;
    setTrades([...updated]);
  };
};