// src/components/FileUploader.js
import React, { useState } from "react";

const FileUploader = ({ apiUrl = "http://localhost:8000", onUploaded = () => {} }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleSelect = (e) => {
    const f = e.target.files[0];
    setFile(f);
  };

  const handleClear = () => setFile(null);

  const handleUpload = async () => {
    if (!file) {
      alert("Select a file first");
      return;
    }
    const form = new FormData();
    form.append("file", file);
    try {
      setUploading(true);
      const res = await fetch(`${apiUrl}/api/upload`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const text = await res.text();
        console.error("Upload failed:", text);
        throw new Error("Upload failed");
      }
      const data = await res.json();
      alert(`Uploaded, inserted: ${data.inserted}`);
      onUploaded();
      setFile(null);
    } catch (err) {
      console.error(err);
      alert("Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded shadow">
      <h2 className="font-semibold mb-3">Upload Production Sheet</h2>
      <div className="border-dashed border-2 border-gray-200 p-6 rounded mb-4">
        <input type="file" onChange={handleSelect} accept=".xlsx, .xls" />
        <div className="mt-3 text-sm text-gray-600">
          {file ? (
            <div>
              <div>Selected: {file.name}</div>
              <div className="mt-2">
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="bg-blue-600 text-white px-4 py-2 rounded mr-2"
                >
                  {uploading ? "Uploading..." : "Upload File"}
                </button>
                <button onClick={handleClear} className="px-3 py-1 rounded border">
                  Clear
                </button>
              </div>
            </div>
          ) : (
            <div>Drag & drop or choose an Excel file (.xlsx / .xls) — Max 10MB</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileUploader;