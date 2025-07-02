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
    console.log(`📝 Field update: ${field} =`, value);

    const updated = [...trades];

    // Handle symbol clearing
    if (field === "symbol" && value.trim() === "") {
      const lookupKeys = getAllFields()
        .map((f) => f.key)
        .filter((k) => k !== "symbol");

      lookupKeys.forEach((k) => {
        if (k.includes(".")) {
          const [parent, child] = k.split(".");
          if (updated[index][parent]) {
            delete updated[index][parent][child];
            if (Object.keys(updated[index][parent]).length === 0) {
              delete updated[index][parent];
            }
          }
        } else {
          delete updated[index][k];
        }
      });
    }

    // Set field value
    const fieldDef = getAllFields().find((f) => f.key === field);
    const valueToSet = fieldDef?.type === "number" ? Number(value) : value;

    if (["trailing_stop_type", "trailing_stop_price"].includes(field)) {
      updated[index][field] = valueToSet;
    } else if (field.includes(".")) {
      const [parentKey, childKey] = field.split(".");
      updated[index][parentKey] = {
        ...(updated[index][parentKey] || {}),
        [childKey]: valueToSet,
      };
    } else {
      updated[index][field] = valueToSet;
    }

    console.log("📦 Trade after update:", updated[index]);

    // Handle actions
    if (field === "action" && valueToSet === "Modify") {
      if (updated[index].order_status !== "--") {
        updated[index].order_status = "Inactive";
        updated[index].trade_status = "--";
        updated[index].action = "--";
        updated[index].editing = true;

        const editableKeys = getAllFields()
          .filter((f) => f.editable === true || f.readonly !== true)
          .map((f) => f.key);

        editableKeys.forEach((key) => {
          const descriptor = Object.getOwnPropertyDescriptor(updated[index], key);
          if (descriptor && descriptor.writable === false) {
            Object.defineProperty(updated[index], key, {
              value: updated[index][key],
              writable: true,
              configurable: true,
              enumerable: true,
            });
          }
        });

        setTrades([...updated]);
      } else {
        alert("❌ This trade is already in draft mode.");
      }
      return;
    }

    if (field === "action" && valueToSet === "Save") {
      updated[index].order_status = "Inactive";
      updated[index].trade_status = "--";
      updated[index].action = "--";
      updated[index].editing = false;

      setTrades([...updated]);

      await fetch("http://localhost:8000/save_trades", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updated),
      });

      return;
    }

    if (field === "action" && valueToSet === "Activate") {
      await handleActivate(index);
      return;
    }

    // Calculate quantity dynamically during draft phase
    const maybeTrade = updated[index];
    const calcQty = calculateQuantity(maybeTrade, portfolio.portfolio_value);
    updated[index].calculated_quantity = calcQty !== null && !isNaN(calcQty) && calcQty > 0 ? calcQty : null;

    // Update trade status for active/pending trades
    if (
      updated[index].order_status === "active" ||
      updated[index].order_status === "Activate Order" ||
      updated[index].trade_status === "pending"
    ) {
      updated[index].order_status = "Activate Order";
      updated[index].trade_status = "--";
    }

    const nestedTrade = flattenToNested(flattenToFlat(updated[index]));

    console.log("🧪 Types of values sent to backend:");
    Object.entries(nestedTrade).forEach(([k, v]) => {
      if (typeof v === "object" && v !== null) {
        Object.entries(v).forEach(([sk, sv]) => {
          console.log(`   ↳ ${k}.${sk}:`, sv, `(${typeof sv})`);
        });
      } else {
        console.log(`→ ${k}:`, v, `(${typeof v})`);
      }
    });

    setTrades([...updated]);
  };
};