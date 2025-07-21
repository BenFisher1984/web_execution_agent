import React from "react";

const LayoutEditor = ({ layoutDraft, setLayoutDraft, onSave, onCancel }) => {
  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-70 flex items-center justify-center">
      <div className="bg-dark-panel border border-gray-600 rounded-lg shadow-2xl w-[90%] max-w-4xl max-h-[90%] overflow-y-auto p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold text-white">Modify Layout</h2>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ✖
          </button>
        </div>

        <div className="space-y-6">
          {layoutDraft.map((section, sIndex) => (
            <div key={sIndex} className="border border-gray-600 rounded p-4 bg-gray-800/50">
              <h3 className="text-md font-bold text-gray-300 mb-2">{section.section}</h3>
              <div className="grid grid-cols-2 gap-2">
                {section.fields.map((field, fIndex) => (
                  <label key={fIndex} className="flex items-center gap-2 text-gray-300">
                    <input
                      type="checkbox"
                      checked={field.enabled !== false}
                      onChange={(e) => {
                        const updated = [...layoutDraft];
                        updated[sIndex].fields[fIndex].enabled = e.target.checked;
                        setLayoutDraft(updated);
                      }}
                      className="accent-blue-500"
                    />
                    <span className="text-sm">{field.label}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onSave}
            className="bg-blue-600 text-white text-sm px-4 py-1 rounded hover:bg-blue-700 transition-colors"
          >
            Save Layout
          </button>
          <button
            onClick={onCancel}
            className="bg-gray-600 text-gray-300 text-sm px-4 py-1 rounded hover:bg-gray-500 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default LayoutEditor;
