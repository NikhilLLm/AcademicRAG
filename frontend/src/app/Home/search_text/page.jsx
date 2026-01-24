"use client";
import { useState } from "react";
import SearchBar from "../components/SearchBar";
import SearchResults from "../components/SearchResults";

export default function SearchPage() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <SearchBar setResults={setResults} setLoading={setLoading} />

      {loading && (
        <p className="text-gray-400 mt-6 text-lg">Searching...</p>
      )}

      {!loading && results.length > 0 && (
        <SearchResults results={results} />
      )}

      {!loading && results.length === 0 && (
        <p className="text-gray-500 mt-6">
          No results yet. Try a search above.
        </p>
      )}
    </div>
  );
}
