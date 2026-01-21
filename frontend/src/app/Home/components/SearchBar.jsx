"use client";
import { useState, useEffect } from "react";
import { Search } from "lucide-react";
import { getSearchResult } from "@/lib/api_call";

export default function SearchBar({ setResults, setLoading }) {
  const [query, setQuery] = useState("");

  // Load query from localStorage on mount
  useEffect(() => {
    const savedQuery = localStorage.getItem("searchQuery");
    if (savedQuery) {
      setQuery(savedQuery);
    }
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;

    // Save query to localStorage
    localStorage.setItem("searchQuery", query);

    setLoading(true);
    try {
      const data = await getSearchResult(query);
      // assuming backend returns { results: [...] }
      setResults(data.results || []);
    } catch (err) {
      console.error("Search failed:", err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-white mb-6">Text Search</h2>

      <div className="flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Enter your search query..."
          className="flex-1 px-6 py-3 rounded-lg bg-[#1a1d2e] text-white placeholder-gray-500 border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
        />
        <button
          onClick={handleSearch}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all flex items-center gap-2 font-medium shadow-lg hover:shadow-blue-500/50"
        >
          <Search className="w-5 h-5" />
          Search
        </button>
      </div>
    </div>
  );
}
