// ResizableTable.js
import React, { useState, useRef, useEffect } from "react";

export default function ResizableTable({ columns, data }) {
  const [colWidths, setColWidths] = useState(() =>
    columns.map(() => 150) // default width in px
  );

  const startX = useRef(null);
  const startWidth = useRef(null);
  const colIndex = useRef(null);

  const handleMouseDown = (e, index) => {
    startX.current = e.clientX;
    startWidth.current = colWidths[index];
    colIndex.current = index;
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  };

  const handleMouseMove = (e) => {
    const deltaX = e.clientX - startX.current;
    const newWidths = [...colWidths];
    newWidths[colIndex.current] = Math.max(60, startWidth.current + deltaX);
    setColWidths(newWidths);
  };

  const handleMouseUp = () => {
    document.removeEventListener("mousemove", handleMouseMove);
    document.removeEventListener("mouseup", handleMouseUp);
  };

  return (
    <table className="table-auto border-collapse text-sm w-full mt-4">
      <thead>
        <tr className="bg-gray-200 text-xs text-gray-700">
          {columns.map((col, i) => (
            <th
              key={col.key}
              className="border px-2 py-1 relative"
              style={{ width: colWidths[i] }}
            >
              <div className="flex justify-between items-center">
                <span>{col.label}</span>
                <div
                  onMouseDown={(e) => handleMouseDown(e, i)}
                  className="w-1 h-full cursor-col-resize bg-gray-300 hover:bg-gray-500"
                  style={{ position: "absolute", right: 0, top: 0, bottom: 0 }}
                ></div>
              </div>
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, rowIndex) => (
          <tr key={rowIndex} className="even:bg-gray-50">
            {columns.map((col, colIndex) => (
              <td
                key={col.key + rowIndex}
                className="border px-2 py-1"
                style={{ width: colWidths[colIndex] }}
              >
                {row[col.key] ?? ""}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
