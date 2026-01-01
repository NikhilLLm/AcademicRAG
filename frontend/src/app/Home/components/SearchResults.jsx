"use client";
import ResultCard from "./ResultCard";

export default function SearchResults({ results }) {
  if (!results || results.length === 0) {
    return (
      <section className="mt-10">
        <h3 className="text-xl font-semibold text-white mb-4">Search Results</h3>
        <p className="text-gray-400">No results found.</p>
      </section>
    );
  }

  return (
    <section className="mt-10 space-y-6">
      <h3 className="text-xl font-semibold text-white mb-4">Search Results</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {results.map((result) => (
          <ResultCard
            key={result.id}
            id={result.id}
            title={result.title}
            collection_name={result.collection_name}
            download_url={result.download_url }
            // extend here if backend returns more fields
            // e.g. author={result.author} id={result.id}
          />
        ))}
      </div>
    </section>
  );
}
