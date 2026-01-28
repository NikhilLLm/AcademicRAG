"use client";

import { useEffect, useState } from "react";
import { MessageSquare, ArrowLeft, Clock, Play, RefreshCw, Plus, Search, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function ChatHistoryPage() {
    const [chats, setChats] = useState([]);
    const [searchQuery, setSearchQuery] = useState("");
    const router = useRouter();

    useEffect(() => {
        const history = JSON.parse(localStorage.getItem("chatHistory")) || [];
        setChats(history);
    }, []);

    const deleteChat = (e, id) => {
        e.preventDefault();
        e.stopPropagation();
        const updated = chats.filter(c => c.id !== id);
        setChats(updated);
        localStorage.setItem("chatHistory", JSON.stringify(updated));
    };

    const filteredChats = chats.filter(chat =>
        chat.title.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-gray-200 p-6 md:p-12 font-sans">
            <div className="max-w-5xl mx-auto">
                {/* Header Section */}
                <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
                    <div>
                        <Link href="/Home" className="group flex items-center gap-2 text-indigo-400 hover:text-indigo-300 transition-colors mb-4 text-sm font-medium w-fit">
                            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                            <span>Back to Dashboard</span>
                        </Link>
                        <h1 className="text-4xl font-extrabold text-white tracking-tight flex items-center gap-3">
                            <MessageSquare className="w-8 h-8 text-indigo-500" />
                            Recent Conversations
                        </h1>
                        <p className="text-gray-500 mt-2">Resume your scientific deep-dives or start new ones.</p>
                    </div>

                    <Link
                        href="/Home"
                        className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-3 rounded-2xl transition-all shadow-lg shadow-indigo-500/20 font-bold"
                    >
                        <Plus className="w-5 h-5" />
                        New Chat from Paper
                    </Link>
                </header>

                {/* Search & Stats */}
                <div className="flex flex-col md:flex-row gap-4 mb-8">
                    <div className="relative flex-1">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-600" />
                        <input
                            type="text"
                            placeholder="Search conversations..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full bg-[#15182b] border border-white/10 rounded-2xl py-3.5 pl-12 pr-4 outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20 transition-all text-sm"
                        />
                    </div>
                    <div className="bg-[#15182b] border border-white/10 rounded-2xl px-6 py-3 flex items-center gap-4 text-sm">
                        <div className="text-gray-500">Active Sessions</div>
                        <div className="text-white font-bold bg-indigo-500/20 px-2 py-0.5 rounded text-indigo-400">{chats.length}</div>
                    </div>
                </div>

                {/* Chat List Grid */}
                {filteredChats.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {filteredChats.map((chat) => (
                            <div
                                key={chat.id}
                                className="group relative bg-[#15182b] border border-white/10 rounded-3xl p-6 transition-all hover:bg-[#1c203a] hover:border-indigo-500/30 hover:shadow-2xl hover:shadow-indigo-500/10"
                            >
                                <div className="flex justify-between items-start mb-4">
                                    <div className="bg-indigo-500/10 p-3 rounded-2xl">
                                        <MessageSquare className="w-6 h-6 text-indigo-400" />
                                    </div>
                                    <button
                                        onClick={(e) => deleteChat(e, chat.id)}
                                        className="p-2 text-gray-600 hover:text-red-400 hover:bg-red-400/10 rounded-xl transition-all opacity-0 group-hover:opacity-100"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>

                                <h3 className="text-lg font-bold text-white mb-2 line-clamp-2 leading-snug group-hover:text-indigo-300 transition-colors">
                                    {chat.title}
                                </h3>

                                <div className="flex items-center gap-2 text-gray-500 text-xs mb-6">
                                    <Clock className="w-3.5 h-3.5" />
                                    <span>Last active {new Date(chat.lastAccessed).toLocaleDateString()}</span>
                                </div>

                                <div className="flex gap-3">
                                    <button
                                        onClick={() => router.push(`/Home/chat/${chat.id}`)}
                                        className="flex-1 flex items-center justify-center gap-2 bg-indigo-500/10 hover:bg-indigo-500 text-indigo-400 hover:text-white px-4 py-2.5 rounded-xl transition-all font-bold text-sm"
                                    >
                                        <Play className="w-4 h-4" />
                                        Resume Chat
                                    </button>
                                    <button
                                        onClick={() => router.push(`/Home/chat/${chat.id}?restart=true`)}
                                        className="flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 text-gray-400 px-4 py-2.5 rounded-xl transition-all font-bold text-sm border border-white/5"
                                    >
                                        <RefreshCw className="w-4 h-4" />
                                        Restart
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-20 bg-[#15182b] border border-dashed border-white/10 rounded-[40px]">
                        <div className="w-20 h-20 bg-indigo-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                            <MessageSquare className="w-10 h-10 text-indigo-500/50" />
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">No conversations found</h3>
                        <p className="text-gray-500 max-w-xs mx-auto mb-8">
                            {searchQuery ? `No matches for "${searchQuery}"` : "Upload a paper and start chatting to see your history here."}
                        </p>
                        {!searchQuery && (
                            <Link
                                href="/Home"
                                className="inline-flex items-center gap-2 text-indigo-400 hover:text-indigo-300 font-bold transition-colors"
                            >
                                Go to library <ArrowLeft className="w-4 h-4 rotate-180" />
                            </Link>
                        )}
                    </div>
                )}
            </div>

            <style jsx global>{`
        body {
          background-color: #0a0a0a;
        }
      `}</style>
        </div>
    );
}