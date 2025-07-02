import React from "react";

const LayoutEditor = ({ layoutDraft, setLayoutDraft, onSave, onCancel }) => {
  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-lg w-[90%] max-w-4xl max-h-[90%] overflow-y-auto p-6">
        <div className="flex justify-between items-center mb-4">
          <div className="space-y-6">
            {layoutDraft.map((section, sIndex) => (
              <div key={sIndex} className="border rounded p-4">
                <h3 className="text-md font-semibold text-gray-700 mb-2">{section.section}</h3>
                <div className="grid grid-cols-2 gap-2">
                  {section.fields.map((field, fIndex) => (
                    <label key={fIndex} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={field.enabled !== false}
                        onChange={(e) => {
                          const updated = [...layoutDraft];
                          updated[sIndex].fields[fIndex].enabled = e.target.checked;
                          setLayoutDraft(updated);
                        }}
                      />
                      <span className="text-sm text-gray-800">{field.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <h2 className="text-lg font-semibold text-gray-800">Modify Layout</h2>
          <button
            onClick={onCancel}
            className="text-gray-500 hover:text-gray-800"
          >
            ✖
          </button>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onSave}
            className="bg-blue-600 text-white text-sm px-4 py-1 rounded hover:bg-blue-700"
          >
            Save Layout
          </button>
          <button
            onClick={onCancel}
            className="bg-gray-300 text-sm px-4 py-1 rounded hover:bg-gray-400"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default LayoutEditor;
