"use client";
import { useState } from "react";
import { Search } from "lucide-react";
import { getSearchResult } from "@/lib/api_call";

export default function SearchBar({ setResults, setLoading }) {
  const [query, setQuery] = useState("");

  const handleSearch = async () => {
    const trimmed = query.trim();
    if (!trimmed) return;

    setLoading(true);

    try {
      // 🔹 Check session cache
      const cached = sessionStorage.getItem("searchData");
      if (cached) {
        const { query: savedQuery, results } = JSON.parse(cached);
        if (savedQuery === trimmed) {
          setResults(results);
          setLoading(false);
          return;
        }
      }

      // 🔹 Fetch new results
      const data = await getSearchResult(trimmed);
      const results = data.results || [];

      // 🔹 Replace old search completely
      sessionStorage.setItem(
        "searchData",
        JSON.stringify({ query: trimmed, results })
      );

      setResults(results);
    } catch (err) {
      console.error("Search failed:", err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // 🔹 Clear results if input is emptied
  const handleChange = (e) => {
    const value = e.target.value;
    setQuery(value);

    if (!value.trim()) {
      sessionStorage.removeItem("searchData");
      setResults([]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") handleSearch();
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-white mb-6">Text Search</h2>

      <div className="flex gap-3">
        <input
          type="text"
          value={query}
          onChange={handleChange}
          onKeyDown={handleKeyPress}
          placeholder="Enter your search query..."
          className="flex-1 px-6 py-3 rounded-lg bg-[#1a1d2e] text-white"
        />

        <button
          onClick={handleSearch}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg flex items-center gap-2"
        >
          <Search className="w-5 h-5" />
          Search
        </button>
      </div>
    </div>
  );
}
