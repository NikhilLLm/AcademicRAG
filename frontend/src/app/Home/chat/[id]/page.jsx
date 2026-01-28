"use client";

import { getChatStatus, sendChatMessage, startChatJob } from "@/lib/api_call";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useState, useRef } from "react";
import { Send, Loader2, Paperclip, ChevronLeft, Maximize2, MoreHorizontal, Bot } from "lucide-react";
import Button from "@/components/ui/Button";
import Link from "next/link";

export default function ChatPage() {
  const { id } = useParams();

  const [chatId, setChatId] = useState(null);
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);

  const searchParams = useSearchParams();
  const restart = searchParams.get("restart");
  const [loadingChat, setLoadingChat] = useState(true);
  const [sending, setSending] = useState(false);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [proMode, setProMode] = useState(false);

  const messagesEndRef = useRef(null);

  // --- LOGIC ---
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (!id) return;
    startChatJob(id).then((res) => setChatId(res.chat_session_id));
  }, [id]);

  useEffect(() => {
    if (!chatId) return;
    const interval = setInterval(async () => {
      const data = await getChatStatus(chatId);
      if (data.status === "done") {
        setLoadingChat(false);
        // Save chat session to history
        saveChatIndex({
          id,
          title: sessionStorage.getItem(`title:${id}`) || "Untitled Paper",
          chatId
        });
        clearInterval(interval);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [chatId]);

  function saveChatIndex({ id, title, chatId }) {
    const chats = JSON.parse(localStorage.getItem("chatHistory")) || [];

    // More robust title retrieval
    let finalTitle = title;
    if (!finalTitle || finalTitle === "Untitled Paper") {
      // Try notes index fallback
      const notes = JSON.parse(localStorage.getItem("notesIndex")) || [];
      const note = notes.find(n => n.id === id);
      if (note) finalTitle = note.title;
    }

    if (chats.some(c => c.id === id)) {
      // Update existing entry with latest chatId and possibly better title
      const index = chats.findIndex(c => c.id === id);
      chats[index] = {
        ...chats[index],
        chatId,
        title: finalTitle !== "Untitled Paper" ? finalTitle : chats[index].title,
        lastAccessed: new Date().toISOString()
      };
    } else {
      chats.unshift({
        id,
        title: finalTitle,
        chatId,
        createdAt: new Date().toISOString(),
        lastAccessed: new Date().toISOString()
      });
    }
    localStorage.setItem("chatHistory", JSON.stringify(chats.slice(0, 10)));
  }

  useEffect(() => {
    // Attempt to get PDF URL from session storage, fallback if needed
    const url = sessionStorage.getItem(`pdf:${id}`);
    if (url) setPdfUrl(url);

    // Load message history or clear if restart
    if (restart === "true") {
      localStorage.removeItem(`chat_msgs:${id}`);
      setMessages([]);
    } else {
      const saved = localStorage.getItem(`chat_msgs:${id}`);
      if (saved) setMessages(JSON.parse(saved));
    }
  }, [id, restart]);

  // Save messages whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem(`chat_msgs:${id}`, JSON.stringify(messages));
    }
  }, [messages, id]);

  const handleSend = async (manualQuery = null) => {
    const textToSend = typeof manualQuery === 'string' ? manualQuery : query;
    if (!textToSend.trim() || sending || loadingChat) return;

    const userMessage = { role: "user", content: textToSend };
    setMessages((prev) => [...prev, userMessage]);
    setQuery("");
    setSending(true);

    try {
      const res = await sendChatMessage(chatId, textToSend);
      setMessages((prev) => [...prev, { role: "assistant", content: res.answer }]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I encountered an error answering that." },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-screen w-full bg-[#0a0a0a] text-gray-200 overflow-hidden font-sans">

      {/* --- LEFT PANEL: PDF VIEWER --- */}
      <div className="w-1/2 flex flex-col border-r border-[#222] bg-[#111]">
        {/* Header */}
        <div className="h-14 px-4 border-b border-[#222] flex items-center justify-between bg-[#111]">
          <div className="flex items-center gap-3">
            <Link href="/Home/chat" className="p-1.5 hover:bg-[#222] rounded-lg transition-colors">
              <ChevronLeft className="w-5 h-5 text-gray-400" />
            </Link>
            <span className="font-semibold text-sm text-gray-200">Your Uploaded Document</span>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-1.5 hover:bg-[#222] rounded-lg text-gray-400">
              <Maximize2 className="w-4 h-4" />
            </button>
            <button className="p-1.5 hover:bg-[#222] rounded-lg text-gray-400">
              <MoreHorizontal className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* PDF Content */}
        <div className="flex-1 bg-[#1a1a1a] relative overflow-hidden">
          {pdfUrl ? (
            <iframe
              src={`${pdfUrl}#view=FitH&toolbar=0&navpanes=0&scrollbar=0`}
              className="w-full h-full border-none"
              title="PDF Preview"
            />
          ) : (
            <div className="flex h-full items-center justify-center flex-col gap-3 text-gray-500">
              <Loader2 className="w-8 h-8 animate-spin" />
              <p className="text-sm">Loading Document...</p>
            </div>
          )}
        </div>
      </div>

      {/* --- RIGHT PANEL: CHAT --- */}
      <div className="w-1/2 flex flex-col bg-[#0a0a0a]">

        {/* Chat Header */}
        <div className="h-14 px-6 border-b border-[#222] flex items-center justify-between bg-[#0a0a0a]">
          <div>
            <h2 className="font-semibold text-white text-sm">Chat with Document</h2>
            <p className="text-xs text-gray-500">Ask questions about the paper</p>
          </div>
          <div className="flex items-center gap-2">
            {/* Status Indicator */}
            {loadingChat ? (
              <span className="text-xs text-yellow-500 bg-yellow-500/10 px-2 py-1 rounded-full flex items-center gap-1">
                <Loader2 className="w-3 h-3 animate-spin" /> Preparing...
              </span>
            ) : (
              <span className="text-xs text-green-500 bg-green-500/10 px-2 py-1 rounded-full">
                Ready
              </span>
            )}
          </div>
        </div>

        {/* Messages List - Custom Scrollbar */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {messages.length === 0 && !loadingChat && (
            <div className="h-full flex flex-col items-center justify-center opacity-50 space-y-4">
              <Bot className="w-12 h-12 text-gray-600" />
              <p className="text-sm text-gray-500 text-center max-w-sm">
                Ask me any question about your notes or content! try asking "Summarize this paper"
              </p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`relative px-5 py-3.5 text-sm leading-relaxed max-w-[85%] shadow-sm ${msg.role === "user"
                  ? "bg-[#3b82f6] text-white rounded-2xl rounded-tr-sm"
                  : "bg-[#252525] text-gray-200 rounded-2xl rounded-tl-sm border border-[#333]"
                  }`}
              >
                {msg.content}
              </div>
            </div>
          ))}

          {sending && (
            <div className="flex w-full justify-start">
              <div className="bg-[#252525] px-4 py-3 rounded-2xl rounded-tl-sm border border-[#333] flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                <span className="text-xs text-gray-400">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 pt-2">
          {/* Contextual Suggestions (Future feature placeholder) */}
          {messages.length === 0 && (
            <div className="flex gap-2 mb-4 overflow-x-auto pb-2 no-scrollbar">
              {["Summarize abstract", "Key contributions?", "Methodology used"].map((s, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(s)}
                  className="text-xs bg-[#1a1a1a] hover:bg-[#252525] border border-[#333] text-gray-400 px-3 py-1.5 rounded-full whitespace-nowrap transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          <div className="bg-[#151515] border border-[#333] rounded-2xl p-2 relative shadow-lg focus-within:border-[#444] transition-colors">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a question here..."
              className="w-full bg-transparent text-gray-200 text-sm px-3 py-2 min-h-[50px] max-h-[120px] resize-none outline-none placeholder:text-gray-600 custom-scrollbar"
              disabled={loadingChat || sending}
            />

            <div className="flex items-center justify-between px-2 pb-1 mt-1">
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <div className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${proMode ? "bg-blue-600 border-blue-600" : "border-gray-600 group-hover:border-gray-500"}`}>
                    {proMode && <svg className="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>}
                  </div>
                  <input
                    type="checkbox"
                    className="hidden"
                    checked={proMode}
                    onChange={() => setProMode(!proMode)}
                  />
                  <span className={`text-xs ${proMode ? "text-blue-400" : "text-gray-500 group-hover:text-gray-400"}`}>Pro Mode</span>
                </label>

                <button className="text-gray-500 hover:text-gray-300 transition-colors">
                  <Paperclip className="w-4 h-4" />
                </button>
              </div>

              <button
                onClick={handleSend}
                disabled={!query.trim() || sending || loadingChat}
                className={`p-2 rounded-xl transition-all ${query.trim() && !sending && !loadingChat
                  ? "bg-[#6366f1] hover:bg-[#5558dd] text-white shadow-lg shadow-indigo-500/20"
                  : "bg-[#222] text-gray-600 cursor-not-allowed"
                  }`}
              >
                {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div className="text-center mt-3">
            <p className="text-[10px] text-gray-700">AI replies may vary. Always double-check with the document.</p>
          </div>
        </div>

      </div>

      {/* Global Styles for Scrollbar */}
      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #333;
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #444;
        }
        .no-scrollbar::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  );
}