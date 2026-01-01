"use client";
import { useState } from "react";
import SearchBar from "../components/SearchBar";
import SearchResults from "../components/SearchResults";

export default function SearchPage() {
  // State for results and loading
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Search input */}
      <SearchBar setResults={setResults} setLoading={setLoading} />

      {/* Loading indicator */}
      {loading && (
        <p className="text-gray-400 mt-6 text-lg">Searching...</p>
      )}

      {/* Results */}
      {!loading && results.length > 0 && (
        <SearchResults results={results} />
      )}

      {/* Empty state */}
      {!loading && results.length === 0 && (
        <p className="text-gray-500 mt-6">No results yet. Try a search above.</p>
      )}
    </div>
  );
}
