"use client";

import { useEffect, useState } from "react";
import { getSearchHistory } from "@/lib/api_call";
import { Clock, Search } from "lucide-react";

export default function HistoryPage() {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function fetchHistory() {
            try {
                const data = await getSearchHistory();
                setHistory(data);
            } catch (err) {
                console.error("Failed to fetch history:", err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        }

        fetchHistory();
    }, []);

    return (
        <div className="min-h-screen px-4 md:px-8 py-8 animate-in fade-in duration-500">
            <div className="max-w-4xl mx-auto">
                <header className="mb-10 text-center md:text-left">
                    <h1 className="text-3xl font-bold text-white mb-2 flex items-center justify-center md:justify-start gap-3">
                        <Clock className="w-8 h-8 text-indigo-400" />
                        Search History
                    </h1>
                    <p className="text-gray-400">Your recent research queries and explorations.</p>
                </header>

                {loading ? (
                    <div className="text-center py-20 text-gray-500 animate-pulse">Loading history...</div>
                ) : error ? (
                    <div className="text-center py-20 text-red-400">Error: {error}</div>
                ) : history.length === 0 ? (
                    <div className="text-center py-20 bg-white/5 rounded-2xl border border-white/10">
                        <Search className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                        <p className="text-gray-400">No search history found.</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {history.map((item) => (
                            <div
                                key={item.id}
                                className="group flex flex-col md:flex-row md:items-center justify-between p-5 bg-[#18181b] hover:bg-[#202024] border border-white/5 hover:border-indigo-500/30 rounded-xl transition-all"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="p-3 bg-white/5 rounded-lg text-gray-400 group-hover:text-indigo-400 transition-colors">
                                        <Search className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h3 className="text-white font-medium text-lg mb-1">{item.query}</h3>
                                        <p className="text-xs text-gray-500">
                                            ID: {item.id}
                                        </p>
                                    </div>
                                </div>

                                <div className="mt-4 md:mt-0 flex items-center gap-4 text-sm text-gray-500">
                                    <span>
                                        {new Date(item.created_at).toLocaleDateString()} • {new Date(item.created_at).toLocaleTimeString()}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
