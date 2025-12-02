// src/App.js
import React, { useEffect, useState } from "react";
import ProductionDashboard from "./components/ProductionDashboard";
import ProductionCard from "./components/ProductionCard";
import FileUploader from "./components/FileUploader";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

function App() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchItems = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/production-items`);
      if (!res.ok) throw new Error("Failed to fetch items");
      const data = await res.json();
      setItems(data.items || []);
    } catch (err) {
      console.error(err);
      alert("Failed to fetch production items");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const handleUploaded = () => {
    // refresh after upload
    fetchItems();
  };

  const handleResetDB = async () => {
    if (!window.confirm("This will delete ALL records. Continue?")) return;
    try {
      const res = await fetch(`${API_URL}/api/reset-db`, { method: "POST" });
      if (!res.ok) throw new Error("Reset failed");
      alert("Database reset successful");
      fetchItems();
    } catch (err) {
      console.error(err);
      alert("Failed to reset DB");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <header className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold">Production Planning Dashboard</h1>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">{items.length} items</span>
            <button
              onClick={handleResetDB}
              className="bg-red-600 text-white px-3 py-1 rounded"
            >
              Reset DB
            </button>
          </div>
        </header>

        <FileUploader apiUrl={API_URL} onUploaded={handleUploaded} />

        <section className="mt-8">
          <ProductionDashboard items={items} />
        </section>

        <section className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading ? (
            <div>Loading...</div>
          ) : items.length === 0 ? (
            <div>No production items yet</div>
          ) : (
            items.map((it) => <ProductionCard key={it.id || it._id} item={it} />)
          )}
        </section>
      </div>
    </div>
  );
}

export default App;